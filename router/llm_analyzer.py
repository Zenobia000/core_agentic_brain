"""
LLM-based Task Analyzer - 使用 LLM 智能分析任務
基於 ReAct 思考模式：Reasoning + Acting
"""

from typing import List, Optional, Dict, Any
from core.types import TaskContext, TaskComplexity, RoutingDecision, AgentRole
from core.simple_logger import log
import json


class LLMTaskAnalyzer:
    """使用 LLM 進行智能任務分析"""

    def __init__(self, llm_provider=None):
        """初始化 LLM 分析器

        Args:
            llm_provider: LLM 提供者實例
        """
        self.llm = llm_provider

    def set_llm(self, llm_provider):
        """設置 LLM 提供者"""
        self.llm = llm_provider

    async def analyze(self, context: TaskContext) -> RoutingDecision:
        """使用 LLM 分析任務並返回路由決策"""
        log('info', summary="LLM analyzing task", prompt=context.prompt[:100])

        if not self.llm:
            # Fallback 到基本分析
            return self._basic_analysis(context)

        try:
            # 構建分析提示
            analysis_prompt = self._build_analysis_prompt(context)

            # 調用 LLM 進行分析
            analysis_result = await self._llm_analyze(analysis_prompt)

            # 解析 LLM 回應
            decision = self._parse_analysis(analysis_result, context)

            log('info', summary=f"LLM analysis complete",
                complexity=decision.complexity.value,
                strategy=decision.strategy,
                agents=[a.value for a in decision.agents])

            return decision

        except Exception as e:
            log('error', summary=f"LLM analysis failed: {e}")
            return self._basic_analysis(context)

    def _build_analysis_prompt(self, context: TaskContext) -> str:
        """構建 LLM 分析提示"""
        return f"""分析以下任務並返回 JSON 格式的路由決策：

任務: {context.prompt}

請分析任務並返回以下格式的 JSON：
{{
    "complexity": "simple|moderate|complex",
    "reasoning": "任務複雜度判斷理由",
    "required_capabilities": ["列出需要的能力"],
    "recommended_agents": ["必須從以下選項中選擇: planner, executor, reviewer"],
    "strategy": "direct|sequential|orchestrated|react",
    "execution_plan": "執行計劃簡述"
}}

重要規則：
1. recommended_agents 必須只包含這三個值: "planner", "executor", "reviewer"
2. 根據複雜度選擇代理：
   - simple: ["executor"]
   - moderate: ["planner", "executor"]
   - complex: ["planner", "executor", "reviewer"]
3. strategy 對應關係：
   - simple → "direct"
   - moderate → "sequential"
   - complex → "orchestrated" 或 "react"

判斷標準：
- simple: 單步驟任務，直接回答或執行
- moderate: 多步驟任務，需要規劃但相對直接
- complex: 需要深度分析、多階段規劃、迭代優化的任務

返回純 JSON，不要其他內容。"""

    async def _llm_analyze(self, prompt: str) -> str:
        """調用 LLM 進行分析"""
        messages = [
            {
                "role": "system",
                "content": """你是任務複雜度分析專家。你必須嚴格返回 JSON 格式。

重要：
1. recommended_agents 只能包含: "planner", "executor", "reviewer"
2. complexity 只能是: "simple", "moderate", "complex"
3. strategy 只能是: "direct", "sequential", "orchestrated", "react"
4. 不要使用其他值，不要使用中文名稱"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # 使用 LLM 生成分析
        response = await self.llm.generate(messages)
        return response.content if hasattr(response, 'content') else str(response)

    def _parse_analysis(self, analysis: str, context: TaskContext) -> RoutingDecision:
        """解析 LLM 分析結果"""
        try:
            # 嘗試提取 JSON
            import re
            json_match = re.search(r'\{.*\}', analysis, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(analysis)

            # 映射複雜度
            complexity_map = {
                "simple": TaskComplexity.SIMPLE,
                "moderate": TaskComplexity.MODERATE,
                "complex": TaskComplexity.COMPLEX
            }
            complexity = complexity_map.get(
                data.get("complexity", "simple").lower(),
                TaskComplexity.SIMPLE
            )

            # 映射代理
            agent_map = {
                "planner": AgentRole.PLANNER,
                "executor": AgentRole.EXECUTOR,
                "reviewer": AgentRole.REVIEWER,
                "orchestrator": AgentRole.ORCHESTRATOR
            }

            agents = []
            for agent_name in data.get("recommended_agents", ["executor"]):
                if agent_name.lower() in agent_map:
                    agents.append(agent_map[agent_name.lower()])

            if not agents:
                agents = [AgentRole.EXECUTOR]

            # 構建決策
            return RoutingDecision(
                strategy=data.get("strategy", "direct"),
                agents=agents,
                complexity=complexity,
                reasoning=data.get("reasoning", "LLM 分析結果"),
                metadata={
                    "llm_analysis": data,
                    "execution_plan": data.get("execution_plan", ""),
                    "required_capabilities": data.get("required_capabilities", [])
                }
            )

        except Exception as e:
            log('error', summary=f"Failed to parse LLM analysis: {e}")
            return self._basic_analysis(context)

    def _basic_analysis(self, context: TaskContext) -> RoutingDecision:
        """基本分析（後備方案）"""
        # 簡單長度判斷
        prompt_length = len(context.prompt)

        if prompt_length < 50:
            complexity = TaskComplexity.SIMPLE
            strategy = "direct"
            agents = [AgentRole.EXECUTOR]
        elif prompt_length < 200:
            complexity = TaskComplexity.MODERATE
            strategy = "sequential"
            agents = [AgentRole.PLANNER, AgentRole.EXECUTOR]
        else:
            complexity = TaskComplexity.COMPLEX
            strategy = "orchestrated"
            agents = [AgentRole.PLANNER, AgentRole.EXECUTOR, AgentRole.REVIEWER]

        return RoutingDecision(
            strategy=strategy,
            agents=agents,
            complexity=complexity,
            reasoning="基本分析（基於任務長度）",
            metadata={"fallback": True}
        )


class ReActAnalyzer(LLMTaskAnalyzer):
    """基於 ReAct 架構的任務分析器

    ReAct = Reasoning + Acting
    每個步驟都包含思考和行動
    """

    def _build_analysis_prompt(self, context: TaskContext) -> str:
        """構建 ReAct 風格的分析提示"""
        return f"""使用 ReAct 方法分析任務：

任務: {context.prompt}

請按照 ReAct 模式分析：

Thought 1: 這個任務的核心目標是什麼？
Reasoning: [分析任務目標]

Thought 2: 完成這個任務需要哪些步驟？
Reasoning: [列出必要步驟]

Thought 3: 每個步驟需要什麼能力？
Reasoning: [分析所需能力]

基於以上分析，返回 JSON 格式的決策：
{{
    "complexity": "評估複雜度: simple|moderate|complex",
    "reasoning": "判斷理由",
    "required_capabilities": ["能力列表"],
    "recommended_agents": ["代理列表"],
    "strategy": "執行策略",
    "execution_plan": "具體執行計劃",
    "react_chain": [
        {{"thought": "思考1", "action": "行動1"}},
        {{"thought": "思考2", "action": "行動2"}}
    ]
}}"""