"""
GeekCode Provider Base - Abstract base classes for LLM providers.

This module defines the interface that all LLM providers must implement,
and provides a factory for creating provider instances.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from geekcode.validation.config import Config


@dataclass
class ProviderResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    provider: str
    token_usage: int = 0
    finish_reason: str = "stop"
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Provider(ABC):
    """
    Abstract base class for LLM providers.

    All provider implementations must inherit from this class and
    implement the required methods.

    Example:
        >>> class OpenAIProvider(Provider):
        ...     def complete(self, prompt, **kwargs):
        ...         # Implementation
        ...         pass
    """

    def __init__(self, model: str, config: Config):
        """
        Initialize the provider.

        Args:
            model: The model identifier.
            config: GeekCode configuration.
        """
        self.model = model
        self.config = config

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass

    @abstractmethod
    def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """
        Generate a completion for the given prompt.

        Args:
            prompt: The prompt to complete.
            conversation_history: Previous conversation messages.
            **kwargs: Additional provider-specific parameters.

        Returns:
            ProviderResponse with the completion.
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Validate that the provider connection is working.

        Returns:
            True if connection is valid, False otherwise.
        """
        pass

    def get_api_key(self) -> Optional[str]:
        """Get the API key for this provider."""
        return self.config.get_api_key(self.provider_name)


class OpenAIProvider(Provider):
    """OpenAI API provider implementation."""

    @property
    def provider_name(self) -> str:
        return "openai"

    def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate completion using OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ImportError("openai package required. Install with: pip install geekcode[openai]")

        api_key = self.get_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        client = openai.OpenAI(api_key=api_key)

        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model.split("/")[-1],  # Remove provider prefix if present
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.config.merged.agent.max_tokens),
            temperature=kwargs.get("temperature", self.config.merged.agent.temperature),
        )

        choice = response.choices[0]
        return ProviderResponse(
            content=choice.message.content,
            model=response.model,
            provider=self.provider_name,
            token_usage=response.usage.total_tokens if response.usage else 0,
            finish_reason=choice.finish_reason,
        )

    def validate_connection(self) -> bool:
        """Validate OpenAI connection."""
        try:
            import openai

            api_key = self.get_api_key()
            if not api_key:
                return False

            client = openai.OpenAI(api_key=api_key)
            client.models.list()
            return True
        except Exception:
            return False


class AnthropicProvider(Provider):
    """Anthropic API provider implementation."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate completion using Anthropic API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic package required. Install with: pip install geekcode[anthropic]"
            )

        api_key = self.get_api_key()
        if not api_key:
            raise ValueError("Anthropic API key not configured")

        client = anthropic.Anthropic(api_key=api_key)

        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model=self.model.split("/")[-1],
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.config.merged.agent.max_tokens),
        )

        return ProviderResponse(
            content=response.content[0].text,
            model=response.model,
            provider=self.provider_name,
            token_usage=response.usage.input_tokens + response.usage.output_tokens,
            finish_reason=response.stop_reason,
        )

    def validate_connection(self) -> bool:
        """Validate Anthropic connection."""
        try:
            import anthropic

            api_key = self.get_api_key()
            if not api_key:
                return False

            client = anthropic.Anthropic(api_key=api_key)
            # Simple validation - just check we can create client
            return True
        except Exception:
            return False


class GoogleProvider(Provider):
    """Google Generative AI provider implementation."""

    @property
    def provider_name(self) -> str:
        return "google"

    def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate completion using Google Generative AI."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai package required. Install with: pip install geekcode[google]"
            )

        api_key = self.get_api_key()
        if not api_key:
            raise ValueError("Google API key not configured")

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(self.model.split("/")[-1])

        # Build chat history
        history = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)

        return ProviderResponse(
            content=response.text,
            model=self.model,
            provider=self.provider_name,
            token_usage=0,  # Google doesn't provide token counts in same way
            finish_reason="stop",
        )

    def validate_connection(self) -> bool:
        """Validate Google connection."""
        try:
            import google.generativeai as genai

            api_key = self.get_api_key()
            if not api_key:
                return False

            genai.configure(api_key=api_key)
            return True
        except Exception:
            return False


class OllamaProvider(Provider):
    """Ollama local provider implementation."""

    @property
    def provider_name(self) -> str:
        return "ollama"

    def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """Generate completion using Ollama."""
        import httpx

        provider_config = self.config.get_provider_config("ollama")
        base_url = provider_config.api_base if provider_config else "http://localhost:11434"

        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            f"{base_url}/api/chat",
            json={
                "model": self.model.split("/")[-1],
                "messages": messages,
                "stream": False,
            },
            timeout=self.config.merged.agent.timeout,
        )
        response.raise_for_status()
        data = response.json()

        return ProviderResponse(
            content=data["message"]["content"],
            model=data.get("model", self.model),
            provider=self.provider_name,
            token_usage=data.get("eval_count", 0),
            finish_reason="stop",
        )

    def validate_connection(self) -> bool:
        """Validate Ollama connection."""
        try:
            import httpx

            provider_config = self.config.get_provider_config("ollama")
            base_url = provider_config.api_base if provider_config else "http://localhost:11434"

            response = httpx.get(f"{base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class OpenAICompatibleProvider(Provider):
    """
    Base for providers that expose an OpenAI-compatible chat completions API.

    Subclasses only need to set _base_url, _env_key, and provider_name.
    Uses httpx (already a core dep) so no extra packages are required.
    """

    _base_url: str = ""
    _env_key: str = ""

    @property
    def provider_name(self) -> str:
        raise NotImplementedError

    def _get_key(self) -> Optional[str]:
        import os

        return self.get_api_key() or os.environ.get(self._env_key)

    def complete(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        import httpx

        api_key = self._get_key()
        if not api_key:
            raise ValueError(
                f"{self.provider_name} API key not configured. "
                f"Set {self._env_key} or add it to config."
            )

        messages = []
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get("max_tokens", self.config.merged.agent.max_tokens),
                "temperature": kwargs.get("temperature", self.config.merged.agent.temperature),
            },
            timeout=self.config.merged.agent.timeout,
        )
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        usage = data.get("usage", {})

        return ProviderResponse(
            content=choice["message"]["content"],
            model=data.get("model", self.model),
            provider=self.provider_name,
            token_usage=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    def validate_connection(self) -> bool:
        try:
            return self._get_key() is not None
        except Exception:
            return False


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter - unified API for 100+ open and commercial models."""

    _base_url = "https://openrouter.ai/api/v1"
    _env_key = "OPENROUTER_API_KEY"

    @property
    def provider_name(self) -> str:
        return "openrouter"


class TogetherProvider(OpenAICompatibleProvider):
    """Together AI - fast inference for open-source models."""

    _base_url = "https://api.together.xyz/v1"
    _env_key = "TOGETHER_API_KEY"

    @property
    def provider_name(self) -> str:
        return "together"


class GroqProvider(OpenAICompatibleProvider):
    """Groq - ultra-fast inference for open models."""

    _base_url = "https://api.groq.com/openai/v1"
    _env_key = "GROQ_API_KEY"

    @property
    def provider_name(self) -> str:
        return "groq"


class ProviderFactory:
    """Factory for creating provider instances."""

    _providers: Dict[str, Type[Provider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
        "ollama": OllamaProvider,
        "openrouter": OpenRouterProvider,
        "together": TogetherProvider,
        "groq": GroqProvider,
    }

    @classmethod
    def register(cls, name: str, provider_class: Type[Provider]) -> None:
        """Register a new provider."""
        cls._providers[name] = provider_class

    @classmethod
    def create(cls, model: str, config: Config) -> Provider:
        """
        Create a provider instance for the given model.

        Args:
            model: Model identifier (e.g., "openai/gpt-4" or "gpt-4").
            config: GeekCode configuration.

        Returns:
            Provider instance.

        Raises:
            ValueError: If the provider is not recognized.
        """
        # Parse provider and model name
        if "/" in model:
            provider_name, model_name = model.split("/", 1)
        else:
            # Try to infer provider from model name
            provider_name = cls._infer_provider(model)
            model_name = model

        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        provider_class = cls._providers[provider_name]
        return provider_class(model=model_name, config=config)

    @classmethod
    def _infer_provider(cls, model: str) -> str:
        """Infer the provider from the model name."""
        model_lower = model.lower()

        if model_lower.startswith("gpt") or model_lower.startswith("o1"):
            return "openai"
        elif model_lower.startswith("claude"):
            return "anthropic"
        elif model_lower.startswith("gemini"):
            return "google"
        elif model_lower.startswith("llama") or model_lower.startswith("deepseek"):
            return "groq"
        elif model_lower.startswith("mixtral") or model_lower.startswith("qwen"):
            return "together"
        elif model_lower in ("codellama", "phi", "phi-2"):
            return "ollama"

        # Default to openrouter (broadest model catalog)
        return "openrouter"

    @classmethod
    def available_providers(cls) -> List[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())
