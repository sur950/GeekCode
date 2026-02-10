"""
GeekCode Configuration - Configuration loading and validation.

This module provides the Config class for managing GeekCode configuration
from local (.geekcode/config.yaml) project-level sources only.
There is no global config — all preferences are per-project.
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

    Handles loading and validating configuration from:
    - Local: .geekcode/config.yaml (project-specific only)

    There is no global config. API keys come from environment variables.

    Example:
        >>> config = Config.load()
        >>> model = config.get_default_model()
        >>> config.set_model("gpt-4")
        >>> config.save()
    """

    LOCAL_CONFIG_DIR = Path(".geekcode")

    def __init__(
        self,
        local_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Config.

        Args:
            local_config: Local (project) configuration dictionary.
        """
        self._local_config = local_config or {}
        self._merged: Optional[GeekCodeConfig] = None

    @classmethod
    def load(cls) -> "Config":
        """
        Load configuration from project-local .geekcode/config.yaml only.

        Returns:
            Config instance with loaded configuration.
        """
        local_config = cls._load_yaml(cls._find_local_config())

        return cls(local_config=local_config)

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
        """Get the configuration as a dictionary."""
        return self._local_config.copy()

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

    def set_model(self, model_name: str) -> None:
        """
        Set the default model.

        Args:
            model_name: The model to set as default.
        """
        if "agent" not in self._local_config:
            self._local_config["agent"] = {}

        self._local_config["agent"]["model"] = model_name
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
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "together": "TOGETHER_API_KEY",
        }

        env_var = env_var_map.get(provider_name)
        if env_var:
            return os.environ.get(env_var)

        return None

    def save(self) -> None:
        """Save configuration to local project config file."""
        local_path = self._find_local_config()
        if local_path:
            self._save_yaml(local_path, self._local_config)

    def _save_yaml(self, path: Path, data: Dict[str, Any]) -> None:
        """Save data to a YAML file."""
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

