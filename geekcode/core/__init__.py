"""
GeekCode core module.

Provides the stateless, filesystem-driven agent architecture.
"""

from geekcode.core.agent import Agent, TaskResult
from geekcode.core.context import ContextEngine
from geekcode.core.cache import CacheEngine

__all__ = ["Agent", "TaskResult", "ContextEngine", "CacheEngine"]
