"""Data models for MCPorter tool definitions, manifests, calls, and results."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolParam(BaseModel):
    """A single parameter for a tool."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = False


class ToolDef(BaseModel):
    """Lean tool definition — what MCPorter stores on disk and uses for lookup."""

    name: str  # e.g. "click"
    server: str  # e.g. "playwright"
    description: str  # one-liner, ~10 words max
    params: List[ToolParam] = Field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        """Full name as ``server.tool`` (e.g. ``playwright.click``)."""
        return f"{self.server}.{self.name}"

    def prompt_line(self) -> str:
        """One-line representation for the LLM prompt fragment."""
        return f"- {self.qualified_name}: {self.description}"

    def full_schema_text(self) -> str:
        """Full parameter schema as text (for on-demand lookup)."""
        lines = [f"Tool: {self.qualified_name}", f"  {self.description}", "  Parameters:"]
        if not self.params:
            lines.append("    (none)")
        for p in self.params:
            req = " (required)" if p.required else ""
            lines.append(f"    - {p.name}: {p.type}{req} — {p.description}")
        return "\n".join(lines)


class ToolManifest(BaseModel):
    """Per-server manifest stored in ``.geekcode/tools/manifests/{server}.yaml``."""

    server_name: str
    command: str
    args: List[str] = Field(default_factory=list)
    tools: List[ToolDef] = Field(default_factory=list)
    fetched_at: str = ""
    full_schema_tokens: int = 0  # how many tokens standard MCP would have cost
    mcporter_tokens: int = 0  # how many tokens MCPorter actually uses

    def token_savings(self) -> int:
        return max(self.full_schema_tokens - self.mcporter_tokens, 0)

    def token_savings_pct(self) -> float:
        if self.full_schema_tokens == 0:
            return 0.0
        return self.token_savings() / self.full_schema_tokens * 100


class ToolCall(BaseModel):
    """Record of a single tool invocation."""

    call_id: str = ""
    tool_name: str = ""  # qualified name: server.tool
    arguments: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""

    def model_post_init(self, __context: Any) -> None:
        if not self.call_id:
            raw = f"{self.tool_name}:{self.arguments}:{datetime.now(timezone.utc).isoformat()}"
            self.call_id = hashlib.sha256(raw.encode()).hexdigest()[:12]
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ToolResult(BaseModel):
    """Result from a tool execution — full output on disk, summary for the agent."""

    call_id: str = ""
    tool_name: str = ""
    success: bool = False
    output: str = ""  # full output (saved to disk)
    summary: str = ""  # short summary (sent to agent)
    error: Optional[str] = None
    duration_ms: int = 0
