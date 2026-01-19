"""
Unified configuration and API key management system.
Provides a single source of truth for all sensitive credentials.
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from app.logger import logger


class ConfigManager:
    """
    Unified configuration manager for API keys and sensitive data.

    Priority order:
    1. Environment variables (highest priority)
    2. .env file
    3. config.toml values (only for non-sensitive config)

    All API keys should ONLY be read from environment variables.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the configuration manager."""
        if not self._initialized:
            self._load_environment()
            self._initialized = True

    def _load_environment(self):
        """Load environment variables from .env file."""
        # Find the .env file in the OpenManus directory
        project_root = Path(__file__).parent.parent
        env_path = project_root / '.env'

        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"Loaded environment from {env_path}")
        else:
            logger.warning(f".env file not found at {env_path}")

    def get_api_key(self, service: str, config_value: Optional[str] = None) -> str:
        """
        Get API key for a specific service.

        Args:
            service: Service name (e.g., 'anthropic', 'openai', 'tavily')
            config_value: Value from config.toml (deprecated, should be empty)

        Returns:
            API key from environment variable

        Raises:
            ValueError: If no API key is found in environment
        """
        # Standardize the environment variable name
        env_key = f"{service.upper()}_API_KEY"

        # Special cases for service names
        if service.lower() == 'llm' or service.lower() == 'claude':
            env_key = "ANTHROPIC_API_KEY"
        elif service.lower() == 'vision':
            # Vision model might use same key as main LLM
            env_key = "ANTHROPIC_API_KEY"

        # 1. Check environment variable (highest priority)
        env_value = os.getenv(env_key)
        if env_value:
            logger.debug(f"Using API key from environment for {service}")
            return env_value

        # 2. Check if config has a non-empty value (deprecated)
        if config_value and config_value not in ["", "YOUR_API_KEY", "YOUR_ANTHROPIC_API_KEY"]:
            logger.warning(
                f"API key found in config.toml for {service}. "
                f"This is deprecated and insecure! Please move to {env_key} in .env file"
            )
            return config_value

        # 3. Raise clear error with instructions
        raise ValueError(
            f"No API key found for {service}.\n"
            f"Please add '{env_key}=your-api-key-here' to your .env file.\n"
            f"If you don't have a .env file, create one in: {Path(__file__).parent.parent / '.env'}"
        )

    def get_optional_api_key(self, service: str, config_value: Optional[str] = None) -> Optional[str]:
        """
        Get optional API key that may not be required.

        Args:
            service: Service name
            config_value: Value from config.toml

        Returns:
            API key if found, None otherwise
        """
        try:
            return self.get_api_key(service, config_value)
        except ValueError:
            logger.debug(f"Optional API key for {service} not found")
            return None

    def get_config_value(self, key: str, default=None):
        """
        Get non-sensitive configuration value.

        Args:
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        # First check environment
        env_value = os.getenv(key.upper())
        if env_value:
            return env_value

        # Return default
        return default

    @classmethod
    def list_required_keys(cls) -> list:
        """List all required API keys for the application."""
        return [
            "ANTHROPIC_API_KEY",  # For Claude models
            "TAVILY_API_KEY",      # For Tavily search (optional)
            "OPENAI_API_KEY",      # For OpenAI models (optional)
            "GOOGLE_API_KEY",      # For Google search (optional)
            "BING_API_KEY",        # For Bing search (optional)
            "DAYTONA_API_KEY",     # For Daytona sandbox (optional)
        ]

    @classmethod
    def check_configuration(cls) -> dict:
        """
        Check which API keys are configured.

        Returns:
            Dictionary with configuration status
        """
        manager = cls()
        status = {}

        for key in cls.list_required_keys():
            env_value = os.getenv(key)
            if env_value:
                # Don't log the actual key, just show it's configured
                status[key] = "✓ Configured"
            else:
                if key == "ANTHROPIC_API_KEY":
                    status[key] = "✗ REQUIRED - Not configured"
                else:
                    status[key] = "○ Optional - Not configured"

        return status


# Global instance
config_manager = ConfigManager()