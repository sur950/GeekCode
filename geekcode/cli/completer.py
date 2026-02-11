"""
GeekCode CLI Completer - prompt_toolkit completion for the REPL.

Provides real-time dropdown suggestions for slash commands and model names.
"""

from typing import Callable, List, Optional

from prompt_toolkit.completion import Completer, Completion


# (command, description) — used for dropdown display
SLASH_COMMANDS = [
    ("/help", "Show help"),
    ("/?", "Show help"),
    ("/status", "Current state, model, cache stats"),
    ("/history", "Recent task history"),
    ("/models", "List available providers and models"),
    ("/model", "Switch model (provider/model-name)"),
    ("/tools", "List MCPorter tools"),
    ("/tools refresh", "Re-fetch tool manifests"),
    ("/tools info", "Show schema for a tool"),
    ("/benchmark run", "Run benchmarks"),
    ("/benchmark report", "Generate benchmark report"),
    ("/loop", "Show coding loop status"),
    ("/loop resume", "Resume interrupted loop"),
    ("/loop reset", "Clear loop checkpoint"),
    ("/newchat", "Start fresh conversation"),
    ("/clear", "Clear screen"),
    ("/reset", "Reset task state"),
    ("/exit", "Exit GeekCode"),
    ("/quit", "Exit GeekCode"),
    ("/q", "Exit GeekCode"),
]

# Static model suggestions (provider/model format)
KNOWN_MODELS = [
    ("openai/gpt-4o", "OpenAI"),
    ("openai/gpt-4o-mini", "OpenAI"),
    ("openai/gpt-4-turbo", "OpenAI"),
    ("openai/o1", "OpenAI"),
    ("openai/o1-mini", "OpenAI"),
    ("anthropic/claude-opus-4-6", "Anthropic"),
    ("anthropic/claude-sonnet-4-5-20250929", "Anthropic"),
    ("anthropic/claude-haiku-4-5-20251001", "Anthropic"),
    ("google/gemini-2.0-flash", "Google"),
    ("google/gemini-2.0-pro", "Google"),
    ("google/gemini-1.5-pro", "Google"),
    ("groq/llama-3.3-70b-versatile", "Groq"),
    ("groq/llama-3.1-8b-instant", "Groq"),
    ("groq/deepseek-r1-distill-llama-70b", "Groq"),
    ("groq/gemma2-9b-it", "Groq"),
    ("together/meta-llama/Llama-3.3-70B-Instruct-Turbo", "Together"),
    ("together/Qwen/Qwen2.5-72B-Instruct-Turbo", "Together"),
    ("together/mistralai/Mixtral-8x22B-Instruct-v0.1", "Together"),
    ("together/deepseek-ai/DeepSeek-R1", "Together"),
    ("openrouter/openai/gpt-4o", "OpenRouter"),
    ("openrouter/anthropic/claude-sonnet-4-5", "OpenRouter"),
    ("openrouter/deepseek/deepseek-r1", "OpenRouter"),
    ("openrouter/meta-llama/llama-3.3-70b-instruct", "OpenRouter"),
]


class GeekCodeCompleter(Completer):
    """Completer for the GeekCode REPL.

    Provides real-time dropdown suggestions:
    - Slash commands with descriptions when typing "/"
    - Model names (provider/model) when typing "/model "
    """

    def __init__(self, ollama_models_fn: Optional[Callable[[], List[str]]] = None):
        self._ollama_models_fn = ollama_models_fn

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Only complete when starting with "/"
        if not text.startswith("/"):
            return

        # /model <partial> — complete model names
        if text.startswith("/model ") and not text.startswith("/models"):
            model_prefix = text[7:]  # after "/model "
            yield from self._complete_model_names(model_prefix)
            return

        # Slash command completion
        for cmd, description in SLASH_COMMANDS:
            if cmd.startswith(text):
                yield Completion(
                    cmd,
                    start_position=-len(text),
                    display_meta=description,
                )

    def _complete_model_names(self, prefix: str):
        """Yield model name completions in provider/model format."""
        prefix_lower = prefix.lower()
        seen = set()

        # Dynamic Ollama models first (from live instance)
        if self._ollama_models_fn:
            try:
                for m in self._ollama_models_fn():
                    full = f"ollama/{m}"
                    if full.lower().startswith(prefix_lower) or m.lower().startswith(prefix_lower):
                        if full not in seen:
                            seen.add(full)
                            yield Completion(
                                full,
                                start_position=-len(prefix),
                                display_meta="Ollama (local)",
                            )
            except Exception:
                pass

        # Static known models
        for model, provider_label in KNOWN_MODELS:
            if model.lower().startswith(prefix_lower) and model not in seen:
                seen.add(model)
                yield Completion(
                    model,
                    start_position=-len(prefix),
                    display_meta=provider_label,
                )
