"""
GeekCode Configuration - Configuration loading and validation.

This module provides the Config class for managing GeekCode configuration
from both global (~/.geekcode/config.yaml) and local (.geekcode/config.yaml)
sources.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class ConfigError(Exception):
    """Raised when there's a configuration error."""

    pass


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""

    api_key: Optional[str] = None
    api_base: Optional[str] = None
    models: List[str] = Field(default_factory=list)
    default_model: Optional[str] = None
    enabled: bool = True


class AgentConfig(BaseModel):
    """Configuration for the agent."""

    model: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120
    retry_count: int = 3


class ProjectConfig(BaseModel):
    """Configuration for the project."""

    name: Optional[str] = None
    description: Optional[str] = None
    include_patterns: List[str] = Field(default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts"])
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["**/node_modules/**", "**/.git/**", "**/__pycache__/**"]
    )


class MCPorterServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    auto_start: bool = False


class MCPorterConfig(BaseModel):
    """Configuration for the MCPorter MCP-to-CLI bridge."""

    enabled: bool = False
    servers: Dict[str, MCPorterServerConfig] = Field(default_factory=dict)


class GeekCodeConfig(BaseModel):
    """Complete GeekCode configuration schema."""

    providers: Dict[str, ProviderConfig] = Field(default_factory=dict)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    mcporter: MCPorterConfig = Field(default_factory=MCPorterConfig)


@dataclass
class ModelInfo:
    """Information about an available model."""

    name: str
    provider: str
    available: bool = True


class Config:
    """
    GeekCode configuration manager.

    Handles loading, merging, and validating configuration from:
    - Global: ~/.geekcode/config.yaml
    - Local: .geekcode/config.yaml (project-specific)

    Local configuration overrides global configuration.

    Example:
        >>> config = Config.load()
        >>> model = config.get_default_model()
        >>> config.set_model("gpt-4", global_=True)
        >>> config.save()
    """

    GLOBAL_CONFIG_DIR = Path.home() / ".geekcode"
    LOCAL_CONFIG_DIR = Path(".geekcode")

    def __init__(
        self,
        global_config: Optional[Dict[str, Any]] = None,
        local_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Config.

        Args:
            global_config: Global configuration dictionary.
            local_config: Local (project) configuration dictionary.
        """
        self._global_config = global_config or {}
        self._local_config = local_config or {}
        self._merged: Optional[GeekCodeConfig] = None

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from default locations.

        Returns:
            Config instance with loaded configuration.
        """
        global_config = cls._load_yaml(cls.GLOBAL_CONFIG_DIR / "config.yaml")
        local_config = cls._load_yaml(cls._find_local_config())

        return cls(global_config=global_config, local_config=local_config)

    @classmethod
    def _load_yaml(cls, path: Optional[Path]) -> Dict[str, Any]:
        """Load YAML file if it exists."""
        if path is None or not path.exists():
            return {}

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except Exception as e:
            raise ConfigError(f"Failed to load config from {path}: {e}")

    @classmethod
    def _find_local_config(cls) -> Optional[Path]:
        """Find the local config file by walking up the directory tree."""
        current = Path.cwd()
        while current != current.parent:
            config_path = current / ".geekcode" / "config.yaml"
            if config_path.exists():
                return config_path
            current = current.parent
        return None

    def get_merged_config(self) -> Dict[str, Any]:
        """Get the merged configuration as a dictionary."""
        merged = self._deep_merge(self._global_config.copy(), self._local_config)
        return merged

    def get_global_config(self) -> Dict[str, Any]:
        """Get the global configuration."""
        return self._global_config

    def get_local_config(self) -> Dict[str, Any]:
        """Get the local configuration."""
        return self._local_config

    @property
    def merged(self) -> GeekCodeConfig:
        """Get the validated merged configuration."""
        if self._merged is None:
            try:
                merged_dict = self.get_merged_config()
                self._merged = GeekCodeConfig(**merged_dict)
            except ValidationError as e:
                raise ConfigError(f"Invalid configuration: {e}")
        return self._merged

    def get_default_model(self) -> Optional[str]:
        """Get the default model from configuration."""
        # Check agent config first
        if self.merged.agent.model:
            return self.merged.agent.model

        # Check providers for default
        for provider_name, provider_config in self.merged.providers.items():
            if provider_config.enabled and provider_config.default_model:
                return f"{provider_name}/{provider_config.default_model}"

        return None

    def get_available_models(self) -> Dict[str, List[ModelInfo]]:
        """Get all available models grouped by provider."""
        models: Dict[str, List[ModelInfo]] = {}

        for provider_name, provider_config in self.merged.providers.items():
            models[provider_name] = []
            for model in provider_config.models:
                available = provider_config.enabled and bool(provider_config.api_key)
                models[provider_name].append(
                    ModelInfo(name=model, provider=provider_name, available=available)
                )

        return models

    def set_model(self, model_name: str, global_: bool = False) -> None:
        """
        Set the default model.

        Args:
            model_name: The model to set as default.
            global_: Whether to set globally or locally.
        """
        config = self._global_config if global_ else self._local_config

        if "agent" not in config:
            config["agent"] = {}

        config["agent"]["model"] = model_name
        self._merged = None  # Reset cache

    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider."""
        return self.merged.providers.get(provider_name)

    def get_api_key(self, provider_name: str) -> Optional[str]:
        """
        Get API key for a provider.

        Checks config first, then environment variables.
        """
        provider = self.get_provider_config(provider_name)
        if provider and provider.api_key:
            return provider.api_key

        # Check environment variables
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
        }

        env_var = env_var_map.get(provider_name)
        if env_var:
            return os.environ.get(env_var)

        return None

    def save(self) -> None:
        """Save configuration to files."""
        self._save_yaml(self.GLOBAL_CONFIG_DIR / "config.yaml", self._global_config)

        local_path = self._find_local_config()
        if local_path:
            self._save_yaml(local_path, self._local_config)

    def _save_yaml(self, path: Path, data: Dict[str, Any]) -> None:
        """Save data to a YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    @classmethod
    def create_default_global(cls) -> Path:
        """Create default global configuration file."""
        config_dir = cls.GLOBAL_CONFIG_DIR
        config_file = config_dir / "config.yaml"

        if config_file.exists():
            return config_file

        config_dir.mkdir(parents=True, exist_ok=True)

        default_config = {
            "providers": {
                "openai": {
                    "api_key": None,  # Set via OPENAI_API_KEY env var
                    "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    "default_model": "gpt-4",
                    "enabled": True,
                },
                "anthropic": {
                    "api_key": None,  # Set via ANTHROPIC_API_KEY env var
                    "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                    "default_model": "claude-3-sonnet",
                    "enabled": True,
                },
                "google": {
                    "api_key": None,  # Set via GOOGLE_API_KEY env var
                    "models": ["gemini-pro", "gemini-pro-vision"],
                    "default_model": "gemini-pro",
                    "enabled": True,
                },
                "ollama": {
                    "api_base": "http://localhost:11434",
                    "models": ["llama2", "codellama", "mistral"],
                    "default_model": "llama2",
                    "enabled": False,
                },
            },
            "agent": {
                "model": None,  # Uses provider default
                "max_tokens": 4096,
                "temperature": 0.7,
                "timeout": 120,
                "retry_count": 3,
            },
        }

        with open(config_file, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

        return config_file
