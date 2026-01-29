"""
Prompt Loader - 統一提示詞管理 (< 100 行)
基於 Linus 原則：消除特殊情況，統一處理
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache


class PromptLoader:
    """統一的提示詞載入器"""

    def __init__(self, prompts_dir: str = "prompts"):
        """初始化提示詞載入器

        Args:
            prompts_dir: 提示詞目錄路徑
        """
        self.prompts_dir = Path(prompts_dir)
        self._cache = {}
        self._load_all_prompts()

    def _load_all_prompts(self):
        """載入所有提示詞檔案"""
        if not self.prompts_dir.exists():
            return

        for yaml_file in self.prompts_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                    if content:
                        # 使用檔案名稱作為命名空間
                        namespace = yaml_file.stem
                        self._cache[namespace] = content
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")

    def get(self, path: str, **kwargs) -> str:
        """獲取提示詞並進行參數替換

        Args:
            path: 提示詞路徑，格式為 "namespace.key" 或 "namespace.section.key"
            **kwargs: 要替換的參數

        Returns:
            格式化後的提示詞字串

        Example:
            loader.get("planning.planning_prompt", user_query="test", history="[]")
            loader.get("tools.python_tool.system")
        """
        parts = path.split('.')
        if not parts:
            return ""

        # 獲取提示詞
        namespace = parts[0]
        if namespace not in self._cache:
            return f"# Prompt not found: {path}"

        # 導航到指定的提示詞
        prompt = self._cache[namespace]
        for part in parts[1:]:
            if isinstance(prompt, dict) and part in prompt:
                prompt = prompt[part]
            else:
                return f"# Prompt not found: {path}"

        # 如果是字串，進行參數替換
        if isinstance(prompt, str):
            try:
                return prompt.format(**kwargs)
            except KeyError as e:
                # 如果缺少參數，返回原始模板
                return prompt

        return str(prompt)

    def get_agent_prompt(self, agent_name: str) -> str:
        """獲取 Agent 的系統提示詞

        Args:
            agent_name: Agent 名稱（如 'planner', 'executor', 'reviewer'）

        Returns:
            該 Agent 的系統提示詞
        """
        # 先嘗試從對應的 YAML 檔案獲取
        prompt = self.get(f"{agent_name.lower()}.system")
        if not prompt.startswith("# Prompt not found"):
            return prompt

        # 如果沒有專門的檔案，從 general.yaml 獲取
        return self.get(f"general.{agent_name.lower()}")

    def get_tool_prompt(self, tool_name: str, action: str = "system") -> str:
        """獲取工具的提示詞

        Args:
            tool_name: 工具名稱（如 'python', 'file', 'browser'）
            action: 動作類型（如 'system', 'execute', 'read'）

        Returns:
            工具的提示詞
        """
        return self.get(f"tools.{tool_name}_tool.{action}")


# 全局實例（單例模式）
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader() -> PromptLoader:
    """獲取全局 PromptLoader 實例"""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader


# 便利函數
def load_prompt(path: str, **kwargs) -> str:
    """直接載入提示詞的便利函數"""
    return get_prompt_loader().get(path, **kwargs)