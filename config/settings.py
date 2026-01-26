"""
配置管理 - 使用 Pydantic Settings
支援環境變數和配置檔案
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path

# 確保載入 .env 檔案（使用專案根目錄）
from dotenv import load_dotenv
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


class RedisSettings(BaseSettings):
    """Redis 配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    class Config:
        env_prefix = "REDIS_"


class QdrantSettings(BaseSettings):
    """Qdrant 配置"""
    host: str = "localhost"
    port: int = 6333
    collection: str = "rag_knowledge_base"
    
    class Config:
        env_prefix = "QDRANT_"


class OpenAISettings(BaseSettings):
    """OpenAI 配置"""
    api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    class Config:
        env_prefix = "OPENAI_"


class SandboxSettings(BaseSettings):
    """沙箱配置"""
    docker_enabled: bool = False
    timeout: int = 30
    memory_limit: str = "512m"
    cpu_limit: int = 50000
    working_dir: str = "/tmp/sandbox"
    
    class Config:
        env_prefix = "SANDBOX_"


class PolicySettings(BaseSettings):
    """策略配置"""
    default_risk_level: str = "medium"
    require_approval_tools: List[str] = ["execute_bash", "file_write", "git_push"]
    max_tool_calls_per_session: int = 50
    
    class Config:
        env_prefix = "POLICY_"


class OpsSettings(BaseSettings):
    """運維配置"""
    enable_tracing: bool = True
    enable_cost_tracking: bool = True
    enable_audit_log: bool = True
    log_retention_days: int = 90
    
    class Config:
        env_prefix = "OPS_"


class Settings(BaseSettings):
    """主配置"""
    
    # 應用設定
    app_name: str = "OpenCode Platform"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # 子配置
    redis: RedisSettings = Field(default_factory=RedisSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)
    policy: PolicySettings = Field(default_factory=PolicySettings)
    ops: OpsSettings = Field(default_factory=OpsSettings)
    
    # API 設定
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_workers: int = 1
    
    # 服務設定
    enabled_services: List[str] = [
        "knowledge_base",
        "sandbox",
        "repo_ops"
    ]
    
    # 插件設定
    plugins: List[str] = []
    
    class Config:
        env_prefix = "OPENCODE_"
        env_nested_delimiter = "__"


# 全域設定實例
settings = Settings()


def get_settings() -> Settings:
    """取得設定實例"""
    return settings


def reload_settings() -> Settings:
    """重新載入設定"""
    global settings
    settings = Settings()
    return settings
