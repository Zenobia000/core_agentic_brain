"""
LLM-based Task Analyzer - 雙階段分析架構

流程:
1. Query Refinement (問題重塑): 理解用戶意圖，重寫為明確目標
2. Routing Decision (路由決策): 基於重塑後的目標，決定 System 1 或 System 2

System 1 (快思考): 意圖明確、單一步驟、無需規劃
System 2 (慢思考): 需要規劃、多步驟、需要迭代審查
"""

from typing import Optional, Dict, Any
from core.types import TaskContext, TaskComplexity, RoutingDecision, AgentRole
from core.prompt_loader import get_prompt_loader
from core.logger import log
import json
import re


class LLMTaskAnalyzer:
    """LLM 任務分析器 - 先理解，再路由"""

    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        self._prompt_loader = get_prompt_loader()

    def set_llm(self, llm_provider):
        self.llm = llm_provider

    async def analyze(self, context: TaskContext) -> RoutingDecision:
        """
        雙階段分析流程:
        1. Query Refinement: 理解並重塑用戶問題
        2. Routing Decision: 基於重塑結果決定執行策略
        """
        prompt_preview = context.prompt[:80] + "..." if len(context.prompt) > 80 else context.prompt
        log.milestone(f"Analysis: {prompt_preview}", phase="router")

        if not self.llm:
            log.warning("No LLM provider, using fallback")
            return self._fallback_analysis(context)

        try:
            # ========== 階段 1: Query Refinement ==========
            log.section("Phase 1: Query Refinement")
            refinement = await self._refine_query(context)

            refined_goal = refinement.get('refined_goal', '')
            refined_preview = refined_goal[:100] + "..." if len(refined_goal) > 100 else refined_goal
            log.detail("intent_type", refinement.get('intent_type', 'unknown'))
            log.detail("ambiguity", refinement.get('ambiguity_level', 'unknown'))
            log.detail("depth", refinement.get('required_depth', 'unknown'))
            log.detail("refined_goal", refined_preview)

            if refinement.get('key_questions'):
                log.detail("questions", refinement.get('key_questions'))

            # ========== 階段 2: Routing Decision ==========
            log.section("Phase 2: Routing Decision")
            decision = self._decide_routing(refinement, context)

            system_mode = decision.metadata.get('system_mode', 'unknown')
            if system_mode == "system_1":
                log.system1(f"Direct execution → {decision.strategy}")
            else:
                log.system2(f"Deep analysis → {decision.strategy}")

            log.detail("complexity", decision.complexity.value)
            log.detail("agents", [a.value for a in decision.agents])

            return decision

        except Exception as e:
            log.failure(f"Analysis failed: {e}")
            return self._fallback_analysis(context)

    async def _refine_query(self, context: TaskContext) -> Dict[str, Any]:
        """
        階段 1: 問題理解與重塑

        不管問題看起來多簡單，都先理解真正的意圖
        Prompts loaded from prompts/router.yaml
        """
        # Load prompts from YAML
        system_prompt = self._prompt_loader.get("router.system")
        refine_prompt = self._prompt_loader.get("router.refine_query", prompt=context.prompt)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": refine_prompt}
        ]

        response = await self.llm.generate(messages)
        content = response.content if hasattr(response, 'content') else str(response)

        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            log.warning(f"Failed to parse refinement JSON: {e}")

        # Fallback: preserve original prompt
        return {
            "original_intent": context.prompt,
            "intent_type": "task_execution",
            "ambiguity_level": "low",
            "key_questions": [],
            "refined_goal": context.prompt,
            "required_depth": "moderate",
            "thought_process": "Fallback: using original prompt"
        }

    def _decide_routing(self, refinement: Dict[str, Any], context: TaskContext) -> RoutingDecision:
        """
        階段 2: 基於重塑結果決定路由

        System 1 條件 (快速執行):
        - 意圖明確 (ambiguity_level: none/low)
        - 簡單類型 (greeting, simple_query)
        - 淺層深度 (required_depth: shallow)

        System 2 條件 (深度規劃):
        - 有歧義 (ambiguity_level: medium/high)
        - 複雜類型 (planning, analysis, creative)
        - 深度需求 (required_depth: moderate/deep)
        """
        intent_type = refinement.get("intent_type", "task_execution")
        ambiguity = refinement.get("ambiguity_level", "low")
        depth = refinement.get("required_depth", "moderate")
        refined_goal = refinement.get("refined_goal", context.prompt)
        thought_process = refinement.get("thought_process", "")

        # ========== System 1 判斷 ==========
        system1_intents = {"greeting", "simple_query"}
        system1_ambiguity = {"none", "low"}
        system1_depth = {"shallow"}

        is_system1 = (
            intent_type in system1_intents or
            (ambiguity in system1_ambiguity and depth in system1_depth)
        )

        if is_system1:
            # System 1: 快速執行
            return RoutingDecision(
                strategy="react",  # 單代理 + 工具循環
                agents=[AgentRole.EXECUTOR],
                complexity=TaskComplexity.SIMPLE,
                reasoning=f"System 1: {intent_type}, low ambiguity, direct execution",
                metadata={
                    "system_mode": "system_1",
                    "refined_goal": refined_goal,
                    "thought_process": thought_process,
                    "intent_type": intent_type,
                    "refinement": refinement
                }
            )

        # ========== System 2 判斷 ==========
        # 根據意圖類型和深度決定具體策略

        # 需要深度規劃的類型
        deep_planning_intents = {"planning", "analysis", "creative"}

        # 需要資訊收集的類型
        info_gathering_intents = {"information_gathering"}

        if intent_type in deep_planning_intents or depth == "deep" or ambiguity in {"medium", "high"}:
            # 完整協調流程: Planner -> Executor -> Reviewer
            strategy = "orchestrated"
            agents = [AgentRole.PLANNER, AgentRole.EXECUTOR, AgentRole.REVIEWER]
            complexity = TaskComplexity.COMPLEX if depth == "deep" else TaskComplexity.MODERATE
            reasoning = f"System 2 (Full): {intent_type}, {ambiguity} ambiguity, requires planning and review"

        elif intent_type in info_gathering_intents:
            # 資訊收集: 單代理 ReAct 但需要多次迭代
            strategy = "react"
            agents = [AgentRole.EXECUTOR]
            complexity = TaskComplexity.MODERATE
            reasoning = f"System 2 (Lite): {intent_type}, information gathering with iteration"

        else:
            # 任務執行: Planner -> Executor
            strategy = "sequential"
            agents = [AgentRole.PLANNER, AgentRole.EXECUTOR]
            complexity = TaskComplexity.MODERATE
            reasoning = f"System 2 (Sequential): {intent_type}, task execution with planning"

        return RoutingDecision(
            strategy=strategy,
            agents=agents,
            complexity=complexity,
            reasoning=reasoning,
            metadata={
                "system_mode": "system_2",
                "refined_goal": refined_goal,
                "thought_process": thought_process,
                "intent_type": intent_type,
                "ambiguity_level": ambiguity,
                "required_depth": depth,
                "key_questions": refinement.get("key_questions", []),
                "refinement": refinement
            }
        )

    def _fallback_analysis(self, context: TaskContext) -> RoutingDecision:
        """後備方案：當 LLM 不可用時"""
        return RoutingDecision(
            strategy="react",
            agents=[AgentRole.EXECUTOR],
            complexity=TaskComplexity.MODERATE,
            reasoning="Fallback: LLM unavailable, using default react strategy",
            metadata={
                "system_mode": "fallback",
                "refined_goal": context.prompt
            }
        )
