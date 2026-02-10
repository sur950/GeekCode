"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest

from geekcode.validation.config import Config, ConfigError, GeekCodeConfig


class TestConfig:
    """Tests for Config class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_get_merged_config(self):
        """Test getting configuration (local-only, no global)."""
        local_config = {
            "agent": {"model": "claude-3"},
            "providers": {
                "openai": {"enabled": True, "models": ["gpt-4"]},
            },
        }

        config = Config(local_config=local_config)
        merged = config.get_merged_config()

        assert merged["agent"]["model"] == "claude-3"
        assert merged["providers"]["openai"]["enabled"] is True

    def test_get_default_model_from_agent(self):
        """Test getting default model from agent config."""
        config = Config(
            local_config={"agent": {"model": "gpt-4-turbo"}},
        )

        assert config.get_default_model() == "gpt-4-turbo"

    def test_get_available_models(self):
        """Test getting available models."""
        config = Config(
            local_config={
                "providers": {
                    "openai": {
                        "enabled": True,
                        "api_key": "test-key",
                        "models": ["gpt-4", "gpt-3.5-turbo"],
                    },
                    "anthropic": {
                        "enabled": False,
                        "models": ["claude-3"],
                    },
                }
            },
        )

        models = config.get_available_models()

        assert "openai" in models
        assert len(models["openai"]) == 2
        assert models["openai"][0].available is True

        assert "anthropic" in models
        assert models["anthropic"][0].available is False

    def test_set_model(self):
        """Test setting the model."""
        config = Config(local_config={})

        config.set_model("gpt-4")
        assert config._local_config["agent"]["model"] == "gpt-4"

    def test_no_global_config_dir(self):
        """Test that there is no global config directory attribute."""
        assert not hasattr(Config, "GLOBAL_CONFIG_DIR")


class TestGeekCodeConfig:
    """Tests for GeekCodeConfig schema."""

    def test_default_config(self):
        """Test creating default configuration."""
        config = GeekCodeConfig()

        assert config.agent.max_tokens == 4096
        assert config.agent.temperature == 0.7
        assert len(config.providers) == 0

    def test_config_with_providers(self):
        """Test configuration with providers."""
        config = GeekCodeConfig(
            providers={
                "openai": {
                    "api_key": "test",
                    "models": ["gpt-4"],
                    "enabled": True,
                }
            }
        )

        assert "openai" in config.providers
        assert config.providers["openai"].enabled is True
