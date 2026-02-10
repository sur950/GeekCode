"""
MCPorter — MCP-to-CLI bridge for GeekCode.

Instead of loading 20K+ tokens of MCP tool schemas into the LLM context,
MCPorter stores lean manifests on disk and sends only tool names + one-line
descriptions to the model (~100 tokens). Tool execution happens as CLI
subprocesses with results written to disk files.

Standard MCP:   LLM <-- 20K tokens schema --> MCP Server <-- full output --> LLM
MCPorter:       LLM <-- ~100 tok names --> Registry --> CLI subprocess --> disk
"""

from geekcode.mcporter.schema import ToolCall, ToolDef, ToolManifest, ToolParam, ToolResult
from geekcode.mcporter.registry import ToolRegistry
from geekcode.mcporter.executor import ToolExecutor

__all__ = [
    "ToolCall",
    "ToolDef",
    "ToolManifest",
    "ToolParam",
    "ToolResult",
    "ToolRegistry",
    "ToolExecutor",
]
