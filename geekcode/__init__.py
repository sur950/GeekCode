"""
GeekCode - Filesystem-driven AI agent for knowledge work.

A stateless CLI that stores everything in .geekcode/ files.
No memory in terminal. Resume anytime. Works across domains.

Domains:
- Coding & Engineering
- Finance & Insurance
- Healthcare
- General Knowledge

Architecture:
- Binary installs to /usr/local/bin (via brew/winget/curl)
- Project state lives in .geekcode/ directory
- Every command reads files → does work → writes files → exits
- Zero CLI memory, full filesystem persistence
"""

__version__ = "1.0.0"
__author__ = "GeekCode Team"
__license__ = "Apache-2.0"

from geekcode.core.agent import Agent, TaskResult
from geekcode.core.context import ContextEngine
from geekcode.core.cache import CacheEngine

__all__ = [
    "Agent",
    "TaskResult",
    "ContextEngine",
    "CacheEngine",
    "__version__",
]
