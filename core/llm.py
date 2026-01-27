"""
LLM 封裝器 - 極簡實作 (< 50 行)
統一的 LLM 介面，支援多個提供者
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from openai import OpenAI


@dataclass
class LLMResponse:
    """LLM 回應結構"""
    content: str
    tool_calls: Optional[List[Dict]] = None
    usage: Optional[Dict] = None


class LLMWrapper:
    """統一的 LLM 介面封裝"""

    def __init__(self, config: Dict[str, Any]):
        """初始化 LLM 客戶端"""
        self.provider = config.get("provider", "openai")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        self._init_client(config)

    def _init_client(self, config):
        """初始化具體的 LLM 客戶端"""
        if self.provider == "openai":
            api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var.")
            self.client = OpenAI(api_key=api_key)
        else:
            raise NotImplementedError(f"Provider {self.provider} not supported")

    async def generate(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """生成 LLM 回應"""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }

            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            return LLMResponse(
                content=message.content or "",
                tool_calls=getattr(message, 'tool_calls', None),
                usage=response.usage.model_dump() if response.usage else None
            )
        except Exception as e:
            return LLMResponse(content=f"LLM Error: {str(e)}")


# 向後相容 LLMClient
LLMClient = LLMWrapper

