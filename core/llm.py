"""
LLM Provider - 統一介面支援多種模型
基於 Linus 原則：消除特殊情況，統一處理
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class LLMResponse:
    """LLM 回應結構"""
    content: str
    tool_calls: Optional[List[Dict]] = None
    usage: Optional[Dict] = None


class LLMProvider:
    """統一的 LLM Provider 介面

    支援：OpenAI, Anthropic, Google, Azure, Ollama
    原則：統一介面，消除特殊情況
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化 LLM Provider

        Args:
            config: LLM 配置，包含 provider、model、api_key 等
        """
        self.provider = config.get("provider", "openai").lower()
        self.model = config.get("model", self._get_default_model())
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 2000)
        self.config = config

        # 初始化客戶端
        self.client = self._init_client()

    def _get_default_model(self) -> str:
        """獲取各 provider 的預設模型"""
        defaults = {
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307",
            "google": "gemini-2.0-flash-exp",
            "azure": "gpt-4o-mini",
            "ollama": "llama3.2"
        }
        return defaults.get(self.provider, "gpt-3.5-turbo")

    def _init_client(self):
        """初始化具體的 LLM 客戶端"""
        # OpenAI（包括相容 API）
        if self.provider in ["openai", "azure", "ollama"]:
            return self._init_openai_compatible()
        # Anthropic
        elif self.provider in ["anthropic", "claude"]:
            return self._init_anthropic()
        # Google
        elif self.provider in ["google", "gemini"]:
            return self._init_google()
        else:
            print(f"Unknown provider {self.provider}, falling back to OpenAI")
            self.provider = "openai"
            return self._init_openai_compatible()

    def _init_openai_compatible(self):
        """初始化 OpenAI 相容的客戶端"""
        from openai import OpenAI, AzureOpenAI

        if self.provider == "azure":
            # Azure OpenAI
            api_key = self.config.get("api_key") or os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = self.config.get("base_url") or os.getenv("AZURE_OPENAI_ENDPOINT")

            if not api_key or not endpoint:
                raise ValueError("Azure config incomplete. Set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT")

            return AzureOpenAI(
                api_key=api_key,
                api_version=self.config.get("api_version", "2024-08-01-preview"),
                azure_endpoint=endpoint
            )

        elif self.provider == "ollama":
            # Ollama 本地模型
            return OpenAI(
                api_key="ollama",  # Ollama 不需要真實 API key
                base_url=self.config.get("base_url", "http://localhost:11434/v1")
            )

        else:
            # 標準 OpenAI
            api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var.")

            return OpenAI(
                api_key=api_key,
                base_url=self.config.get("base_url", "https://api.openai.com/v1")
            )

    def _init_anthropic(self):
        """初始化 Anthropic 客戶端"""
        try:
            import anthropic
        except ImportError:
            print("Anthropic not installed. Install with: pip install anthropic")
            return self._fallback_to_openai()

        api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY env var.")

        return anthropic.Anthropic(api_key=api_key)

    def _init_google(self):
        """初始化 Google 客戶端"""
        # 使用 OpenAI 相容端點
        api_key = self.config.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key not found. Set GOOGLE_API_KEY env var.")

        from openai import OpenAI
        return OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )

    def _fallback_to_openai(self):
        """降級到 OpenAI"""
        print("Falling back to OpenAI...")
        self.provider = "openai"
        return self._init_openai_compatible()

    async def generate(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """生成 LLM 回應 - 統一介面

        Args:
            messages: 對話訊息列表
            tools: 工具定義（可選）

        Returns:
            LLMResponse 物件
        """
        try:
            # Anthropic 特殊處理
            if self.provider in ["anthropic", "claude"]:
                return await self._generate_anthropic(messages, tools)

            # 其他使用 OpenAI 相容 API
            return await self._generate_openai_compatible(messages, tools)

        except Exception as e:
            print(f"LLM Error ({self.provider}): {e}")
            return LLMResponse(content=f"Error: {str(e)}")

    async def _generate_openai_compatible(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """OpenAI 相容 API 生成"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        # Azure 特殊處理
        if self.provider == "azure":
            deployment = self.config.get("deployment_id") or os.getenv("AZURE_OPENAI_DEPLOYMENT")
            if deployment:
                kwargs["model"] = deployment

        # 工具支援
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

    async def _generate_anthropic(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> LLMResponse:
        """Anthropic 專用生成"""
        # 分離系統訊息
        system_msg = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_messages.append(msg)

        # Anthropic API 調用
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": user_messages
        }

        if system_msg:
            kwargs["system"] = system_msg

        # 工具支援（如果 Anthropic 支援）
        if tools:
            # Anthropic 工具格式可能不同
            pass

        response = self.client.messages.create(**kwargs)

        return LLMResponse(
            content=response.content[0].text if response.content else "",
            tool_calls=None,  # Anthropic 工具調用格式不同
            usage={"total_tokens": response.usage.total_tokens} if hasattr(response, 'usage') else None
        )

    # 簡化的同步介面（向後相容）
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """同步對話介面（向後相容）"""
        import asyncio

        async def _chat():
            response = await self.generate(messages)
            return response.content

        # 在同步環境中運行異步函數
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已有事件循環在運行（Jupyter 等環境）
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(_chat())
            else:
                return asyncio.run(_chat())
        except:
            # 最後的降級方案
            return asyncio.run(_chat())


# 向後相容
LLMWrapper = LLMProvider
LLMClient = LLMProvider


def get_llm_provider(config: Optional[Dict] = None) -> LLMProvider:
    """工廠函數：獲取 LLM Provider 實例

    Args:
        config: LLM 配置

    Returns:
        LLMProvider 實例
    """
    if config is None:
        # 使用預設配置
        config = {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 2000
        }

    return LLMProvider(config)