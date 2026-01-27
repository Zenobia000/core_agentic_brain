"""
Unit tests for configuration module.
"""

import pytest
import os
from pathlib import Path
from core.config import ConfigLoader


class TestConfigLoader:
    """Test ConfigLoader class"""

    def test_load_minimal_config(self):
        """Test loading minimal configuration"""
        loader = ConfigLoader(mode="minimal")
        config = loader.config

        assert "llm" in config
        assert "tools" in config
        assert config["llm"]["provider"] == "openai"
        assert "enabled" in config["tools"]

    def test_load_standard_config(self):
        """Test loading standard configuration"""
        loader = ConfigLoader(mode="standard")
        config = loader.config

        assert "llm" in config
        assert "tools" in config
        assert "router" in config
        assert "agents" in config

    def test_env_override(self, monkeypatch):
        """Test environment variable override"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        monkeypatch.setenv("LLM_MODEL", "gpt-4")

        loader = ConfigLoader(mode="minimal")
        config = loader.config

        assert config["llm"]["api_key"] == "test-key-123"
        assert config["llm"]["model"] == "gpt-4"

    def test_config_merge(self):
        """Test configuration merging"""
        loader = ConfigLoader(mode="minimal")
        custom = {"llm": {"temperature": 0.5}}

        merged = loader._merge_configs(loader.config, custom)

        assert merged["llm"]["temperature"] == 0.5
        assert "provider" in merged["llm"]  # Original key preserved

    def test_invalid_mode(self):
        """Test invalid configuration mode"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader(mode="invalid")

    def test_get_method(self):
        """Test get method with dot notation"""
        loader = ConfigLoader(mode="minimal")

        assert loader.get("llm.provider") == "openai"
        assert loader.get("nonexistent", "default") == "default"
        assert loader.get("llm.nonexistent") is None