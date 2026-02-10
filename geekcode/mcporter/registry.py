"""Tool registry — discovers, caches, and serves lean tool manifests."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from geekcode.mcporter.schema import ToolDef, ToolManifest, ToolParam
from geekcode.mcporter.transport import MCPTransport


class ToolRegistry:
    """
    Manages MCP tool manifests on disk.

    On ``refresh()``, connects to MCP servers, fetches full tool schemas,
    and writes *lean* manifests to ``.geekcode/tools/manifests/``.

    On ``build_prompt_fragment()``, reads manifests from disk and returns
    only tool names + one-line descriptions (~100 tokens total).
    """

    def __init__(self, geekcode_dir: Path):
        self._geekcode_dir = geekcode_dir
        self._manifests_dir = geekcode_dir / "tools" / "manifests"
        self._manifests_dir.mkdir(parents=True, exist_ok=True)

    # ── Manifest I/O ──────────────────────────────────────────────────────

    def load_manifests(self) -> Dict[str, ToolManifest]:
        """Load all cached manifests from disk."""
        manifests: Dict[str, ToolManifest] = {}
        for path in self._manifests_dir.glob("*.yaml"):
            try:
                with open(path) as f:
                    data = yaml.safe_load(f) or {}
                manifests[path.stem] = ToolManifest(**data)
            except Exception:
                continue
        return manifests

    def _write_manifest(self, manifest: ToolManifest) -> None:
        path = self._manifests_dir / f"{manifest.server_name}.yaml"
        with open(path, "w") as f:
            yaml.dump(manifest.model_dump(), f, default_flow_style=False, sort_keys=False)

    # ── Refresh from MCP servers ──────────────────────────────────────────

    def refresh(self, server_config: Optional[Dict] = None, server_name: Optional[str] = None) -> ToolManifest:
        """
        Connect to an MCP server, fetch tools, and write a lean manifest.

        Parameters
        ----------
        server_config : dict with ``command``, ``args``, ``env``
        server_name : name for this server (e.g. "playwright")
        """
        if not server_config or not server_name:
            raise ValueError("server_config and server_name are required")

        transport = MCPTransport(
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env", {}),
        )

        try:
            transport.start()
            transport.initialize()
            raw_tools = transport.list_tools()
        finally:
            transport.stop()

        # Convert raw MCP tool schemas to lean ToolDefs
        tools: List[ToolDef] = []
        full_schema_chars = 0

        for raw in raw_tools:
            full_schema_chars += len(str(raw))  # approximate original size

            params: List[ToolParam] = []
            input_schema = raw.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            required = set(input_schema.get("required", []))

            for pname, pinfo in properties.items():
                params.append(ToolParam(
                    name=pname,
                    type=pinfo.get("type", "string"),
                    description=pinfo.get("description", "")[:80],
                    required=pname in required,
                ))

            desc = raw.get("description", "")
            # Truncate description to one line for the lean manifest
            short_desc = desc.split("\n")[0][:100] if desc else raw["name"]

            tools.append(ToolDef(
                name=raw["name"],
                server=server_name,
                description=short_desc,
                params=params,
            ))

        # Estimate tokens (4 chars ≈ 1 token)
        full_schema_tokens = full_schema_chars // 4
        prompt_fragment = "\n".join(t.prompt_line() for t in tools)
        mcporter_tokens = len(prompt_fragment) // 4

        manifest = ToolManifest(
            server_name=server_name,
            command=server_config["command"],
            args=server_config.get("args", []),
            tools=tools,
            fetched_at=datetime.now(timezone.utc).isoformat(),
            full_schema_tokens=full_schema_tokens,
            mcporter_tokens=mcporter_tokens,
        )

        self._write_manifest(manifest)
        return manifest

    # ── Tool Lookup ───────────────────────────────────────────────────────

    def get_tool(self, qualified_name: str) -> Optional[ToolDef]:
        """Lookup a tool by ``server.tool_name``."""
        manifests = self.load_manifests()
        for manifest in manifests.values():
            for tool in manifest.tools:
                if tool.qualified_name == qualified_name:
                    return tool
        return None

    def list_tools(self) -> List[ToolDef]:
        """Return all tools across all servers."""
        tools: List[ToolDef] = []
        for manifest in self.load_manifests().values():
            tools.extend(manifest.tools)
        return tools

    # ── Prompt Building ───────────────────────────────────────────────────

    def build_prompt_fragment(self) -> str:
        """
        Build a lean tool list for the LLM prompt.

        Returns something like::

            Available tools:
            - playwright.click: Click an element on the page
            - playwright.screenshot: Take a screenshot
            Use tool: <tool_name> with {param: value} to invoke.

        This is ~100 tokens instead of the ~20K a full MCP schema would cost.
        """
        tools = self.list_tools()
        if not tools:
            return ""

        lines = ["Available tools:"]
        for tool in tools:
            lines.append(tool.prompt_line())
        lines.append('Use tool: <tool_name> with {"param": "value"} to invoke.')
        return "\n".join(lines)

    def build_full_schema(self, qualified_name: str) -> str:
        """Return full parameter schema for ONE tool (on-demand only)."""
        tool = self.get_tool(qualified_name)
        if not tool:
            return f"Tool not found: {qualified_name}"
        return tool.full_schema_text()

    # ── Reporting ─────────────────────────────────────────────────────────

    def token_savings_report(self) -> Dict[str, Dict]:
        """Report token savings per server."""
        report: Dict[str, Dict] = {}
        for name, manifest in self.load_manifests().items():
            report[name] = {
                "tools_count": len(manifest.tools),
                "standard_mcp_tokens": manifest.full_schema_tokens,
                "mcporter_tokens": manifest.mcporter_tokens,
                "tokens_saved": manifest.token_savings(),
                "savings_pct": f"{manifest.token_savings_pct():.1f}%",
            }
        return report
