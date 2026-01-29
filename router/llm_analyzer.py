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
from core.logger import logger
import json
import re


class LLMTaskAnalyzer:
    """LLM 任務分析器 - 先理解，再路由"""

    def __init__(self, llm_provider=None):
        self.llm = llm_provider

    def set_llm(self, llm_provider):
        self.llm = llm_provider

    async def analyze(self, context: TaskContext) -> RoutingDecision:
        """
        雙階段分析流程:
        1. Query Refinement: 理解並重塑用戶問題
        2. Routing Decision: 基於重塑結果決定執行策略
        """
        prompt_preview = context.prompt[:80] + "..." if len(context.prompt) > 80 else context.prompt
        logger.info(f"[LLM Analyzer] Starting analysis: {prompt_preview}")

        if not self.llm:
            logger.warning("[LLM Analyzer] No LLM provider, using fallback")
            return self._fallback_analysis(context)

        try:
            # ========== 階段 1: Query Refinement ==========
            logger.info("=" * 50)
            logger.info("[Phase 1] Query Understanding & Refinement")
            refinement = await self._refine_query(context)

            refined_goal = refinement.get('refined_goal', '')
            refined_preview = refined_goal[:100] + "..." if len(refined_goal) > 100 else refined_goal
            logger.info(f"  - Original Intent: {refinement.get('original_intent', 'N/A')[:80]}")
            logger.info(f"  - Intent Type: {refinement.get('intent_type', 'unknown')}")
            logger.info(f"  - Ambiguity Level: {refinement.get('ambiguity_level', 'unknown')}")
            logger.info(f"  - Required Depth: {refinement.get('required_depth', 'unknown')}")
            logger.info(f"  - Refined Goal: {refined_preview}")

            if refinement.get('key_questions'):
                logger.info(f"  - Key Questions: {refinement.get('key_questions')}")

            # ========== 階段 2: Routing Decision ==========
            logger.info("=" * 50)
            logger.info("[Phase 2] Routing Decision based on Refined Goal")
            decision = self._decide_routing(refinement, context)

            system_mode = decision.metadata.get('system_mode', 'unknown')
            mode_emoji = "⚡" if system_mode == "system_1" else "🧠"
            logger.info(f"  - System Mode: {mode_emoji} {system_mode.upper()}")
            logger.info(f"  - Complexity: {decision.complexity.value}")
            logger.info(f"  - Strategy: {decision.strategy}")
            logger.info(f"  - Agents: {[a.value for a in decision.agents]}")
            reasoning_preview = decision.reasoning[:100] + "..." if len(decision.reasoning) > 100 else decision.reasoning
            logger.info(f"  - Reasoning: {reasoning_preview}")
            logger.info("=" * 50)

            return decision

        except Exception as e:
            logger.error(f"[LLM Analyzer] Analysis failed: {e}")
            return self._fallback_analysis(context)

    async def _refine_query(self, context: TaskContext) -> Dict[str, Any]:
        """
        階段 1: 問題理解與重塑

        不管問題看起來多簡單，都先理解真正的意圖
        """
        prompt = f"""你是問題理解專家。請分析用戶的請求並重塑為明確的執行目標。

## 用戶原始請求
{context.prompt}

## 分析框架
1. **Intent Recognition (意圖識別)**: 用戶真正想要什麼？
2. **Ambiguity Detection (歧義檢測)**: 有哪些不明確的地方？
3. **Goal Refinement (目標重塑)**: 將模糊請求重寫為明確、可執行的目標

## 意圖類型 (intent_type)
- greeting: 打招呼、閒聊
- simple_query: 簡單問答（有明確答案）
- information_gathering: 需要搜尋資訊
- task_execution: 需要執行具體任務（寫代碼、操作文件等）
- planning: 需要制定計劃（旅遊、項目規劃等）
- analysis: 需要分析或比較
- creative: 創作內容

## JSON 輸出格式
{{
    "original_intent": "用一句話概括用戶的原始意圖",
    "intent_type": "greeting|simple_query|information_gathering|task_execution|planning|analysis|creative",
    "ambiguity_level": "none|low|medium|high",
    "key_questions": ["如果有歧義，列出需要釐清的問題"],
    "refined_goal": "重塑後的明確目標（這將作為執行的依據）",
    "required_depth": "shallow|moderate|deep",
    "thought_process": "簡述你的分析過程"
}}"""

        messages = [
            {"role": "system", "content": "你是問題理解專家。只返回 JSON。"},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm.generate(messages)
        content = response.content if hasattr(response, 'content') else str(response)

        try:
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"Failed to parse refinement JSON: {e}")

        # Fallback: 保留原始問題
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
