"""Tool executor — runs MCP tool calls via CLI subprocesses, saves results to disk."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Optional

import yaml

from geekcode.mcporter.registry import ToolRegistry
from geekcode.mcporter.schema import ToolCall, ToolResult
from geekcode.mcporter.transport import MCPTransport, MCPTransportError


class ToolExecutor:
    """
    Executes MCP tool calls and persists results to disk.

    Full tool output is written to ``.geekcode/tools/results/{call_id}.yaml``.
    A short summary is returned to the agent — the LLM never sees the full
    raw output unless the agent explicitly reads the file.
    """

    def __init__(self, registry: ToolRegistry, geekcode_dir: Path):
        self._registry = registry
        self._results_dir = geekcode_dir / "tools" / "results"
        self._results_dir.mkdir(parents=True, exist_ok=True)
        self._transports: Dict[str, MCPTransport] = {}
        self._server_configs: Dict[str, Dict] = {}

    def set_server_configs(self, configs: Dict[str, Dict]) -> None:
        """Store server configs for lazy transport creation."""
        self._server_configs = configs

    # ── Execution ─────────────────────────────────────────────────────────

    def execute(self, tool_name: str, arguments: Optional[Dict] = None) -> ToolResult:
        """
        Execute a tool call and save the result to disk.

        Parameters
        ----------
        tool_name : qualified name like ``playwright.click``
        arguments : dict of parameter values
        """
        call = ToolCall(tool_name=tool_name, arguments=arguments or {})

        # Look up tool definition
        tool_def = self._registry.get_tool(tool_name)
        if not tool_def:
            result = ToolResult(
                call_id=call.call_id,
                tool_name=tool_name,
                success=False,
                error=f"Tool not found: {tool_name}. Run /tools refresh to update manifests.",
            )
            self._save_result(result)
            return result

        # Get or start transport for this server
        try:
            transport = self._get_transport(tool_def.server)
        except MCPTransportError as exc:
            result = ToolResult(
                call_id=call.call_id,
                tool_name=tool_name,
                success=False,
                error=str(exc),
            )
            self._save_result(result)
            return result

        # Execute the tool call
        t0 = time.perf_counter()
        try:
            raw_result = transport.call_tool(tool_def.name, arguments or {})
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            # Extract output text from MCP result
            content_parts = raw_result.get("content", [])
            output_parts = []
            for part in content_parts:
                if isinstance(part, dict):
                    output_parts.append(part.get("text", str(part)))
                else:
                    output_parts.append(str(part))
            full_output = "\n".join(output_parts) if output_parts else str(raw_result)

            result = ToolResult(
                call_id=call.call_id,
                tool_name=tool_name,
                success=True,
                output=full_output,
                summary=self.summarize(full_output),
                duration_ms=elapsed_ms,
            )

        except MCPTransportError as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            result = ToolResult(
                call_id=call.call_id,
                tool_name=tool_name,
                success=False,
                error=str(exc),
                duration_ms=elapsed_ms,
            )

        self._save_result(result)
        return result

    # ── Result Persistence ────────────────────────────────────────────────

    def _save_result(self, result: ToolResult) -> None:
        path = self._results_dir / f"{result.call_id}.yaml"
        with open(path, "w") as f:
            yaml.dump(result.model_dump(), f, default_flow_style=False, sort_keys=False)

    def get_result(self, call_id: str) -> Optional[ToolResult]:
        """Read a previously-saved result from disk."""
        path = self._results_dir / f"{call_id}.yaml"
        if not path.exists():
            return None
        with open(path) as f:
            data = yaml.safe_load(f)
        return ToolResult(**data) if data else None

    # ── Summarization ─────────────────────────────────────────────────────

    @staticmethod
    def summarize(output: str, max_chars: int = 500) -> str:
        """Create a short summary of tool output for the agent."""
        if not output:
            return "(empty output)"
        if len(output) <= max_chars:
            return output
        # Take first and last portion
        head = output[: max_chars // 2]
        tail = output[-(max_chars // 2) :]
        omitted = len(output) - max_chars
        return f"{head}\n... [{omitted} chars omitted — full output on disk] ...\n{tail}"

    # ── Transport Management ──────────────────────────────────────────────

    def _get_transport(self, server: str) -> MCPTransport:
        """Get or lazily create a transport for a server."""
        if server in self._transports and self._transports[server].is_running:
            return self._transports[server]

        config = self._server_configs.get(server)
        if not config:
            raise MCPTransportError(
                f"No server config for '{server}'. "
                "Add it to mcporter.servers in .geekcode/config.yaml"
            )

        transport = MCPTransport(
            command=config["command"],
            args=config.get("args", []),
            env=config.get("env", {}),
        )
        transport.start()
        transport.initialize()
        self._transports[server] = transport
        return transport

    def cleanup(self) -> None:
        """Stop all running MCP server subprocesses."""
        for transport in self._transports.values():
            transport.stop()
        self._transports.clear()

    def __del__(self):
        self.cleanup()
