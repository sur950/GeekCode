"""MCP server communication via stdio subprocess transport."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MCPTransportError(Exception):
    """Raised when MCP transport communication fails."""


class MCPTransport:
    """
    Communicate with an MCP server over stdin/stdout (JSON-RPC).

    The subprocess is started lazily on first use and stopped explicitly
    via ``stop()`` or when the transport is garbage-collected.
    """

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        self.command = command
        self.args = args or []
        self.env = env or {}
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._lock = threading.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self) -> None:
        """Spawn the MCP server subprocess."""
        if self._process and self._process.poll() is None:
            return  # already running

        merged_env = {**os.environ, **self.env}
        try:
            self._process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=merged_env,
            )
        except FileNotFoundError:
            raise MCPTransportError(
                f"MCP server command not found: {self.command}. "
                "Make sure the package is installed (e.g. npx @anthropic/mcp-playwright)."
            )

    def stop(self) -> None:
        """Terminate the MCP server subprocess."""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
        self._process = None

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    # ── JSON-RPC ──────────────────────────────────────────────────────────

    def send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a JSON-RPC request and return the result."""
        if not self.is_running:
            self.start()

        with self._lock:
            self._request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
            }
            if params:
                request["params"] = params

            line = json.dumps(request) + "\n"

            try:
                self._process.stdin.write(line.encode())
                self._process.stdin.flush()

                raw = self._process.stdout.readline()
                if not raw:
                    raise MCPTransportError("MCP server closed connection (empty response)")

                response = json.loads(raw.decode())
            except (BrokenPipeError, OSError) as exc:
                raise MCPTransportError(f"MCP transport error: {exc}")

        if "error" in response:
            err = response["error"]
            raise MCPTransportError(f"MCP error {err.get('code')}: {err.get('message')}")

        return response.get("result", {})

    # ── MCP Protocol ──────────────────────────────────────────────────────

    def initialize(self) -> Dict[str, Any]:
        """Perform MCP initialize handshake."""
        return self.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "geekcode-mcporter", "version": "0.1.0"},
        })

    def list_tools(self) -> List[Dict[str, Any]]:
        """Fetch the tool list from the MCP server."""
        result = self.send("tools/list")
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        return self.send("tools/call", {"name": name, "arguments": arguments or {}})

    # ── Cleanup ───────────────────────────────────────────────────────────

    def __del__(self):
        self.stop()
