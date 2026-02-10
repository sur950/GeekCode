"""
GeekCode CLI - Interactive chat interface.

Run `geekcode` to start the agent in current directory.
All state managed in .geekcode/ files.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from geekcode import __version__

console = Console()


def find_workspace() -> Path:
    """Find workspace root (has .geekcode/) or use current directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".geekcode").exists():
            return current
        current = current.parent
    return Path.cwd()


def _detect_ollama() -> bool:
    """Check if Ollama is running locally."""
    try:
        import httpx
        r = httpx.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


MODEL_CHOICES = [
    ("ollama/llama3", "Ollama (local, no API key)", None),
    ("openrouter/deepseek/deepseek-r1", "OpenRouter (100+ models, free API key)", "OPENROUTER_API_KEY"),
    ("groq/llama-3.3-70b-versatile", "Groq (fast, free tier)", "GROQ_API_KEY"),
    ("claude-sonnet-4-5", "Anthropic", "ANTHROPIC_API_KEY"),
    ("gpt-4o", "OpenAI", "OPENAI_API_KEY"),
    ("gemini-2.0-flash", "Google", "GOOGLE_API_KEY"),
    ("together/mixtral-8x7b", "Together AI", "TOGETHER_API_KEY"),
]


def _run_first_time_setup(workspace: Path) -> dict:
    """Interactive setup on first run. Returns config dict."""
    console.print()
    console.print("[bold blue]Welcome to GeekCode![/bold blue]")
    console.print(f"[dim]Setting up project: {workspace.name}[/dim]\n")

    # 1. Model selection — auto-detect Ollama
    ollama_running = _detect_ollama()

    console.print("[bold]Which LLM would you like to use?[/bold]")

    if ollama_running:
        # Ollama detected — show it first as recommended
        display_choices = list(MODEL_CHOICES)  # already has ollama first
        for i, (model_name, label, _) in enumerate(display_choices, 1):
            suffix = ""
            if "ollama" in model_name:
                suffix = " [green]<- recommended (detected, local)[/green]"
            console.print(f"  [cyan][{i}][/cyan] {model_name} ({label}){suffix}")
    else:
        # Ollama not running — reorder: OpenRouter first, Ollama gets "(not running)" note
        display_choices = []
        for m, l, k in MODEL_CHOICES:
            if "ollama" in m:
                display_choices.append((m, l + " (not running)", k))
            else:
                display_choices.append((m, l, k))
        # Move OpenRouter to position 0 (swap with ollama)
        ollama_idx = next((i for i, (m, _, _) in enumerate(display_choices) if "ollama" in m), 0)
        or_idx = next((i for i, (m, _, _) in enumerate(display_choices) if "openrouter" in m), 1)
        display_choices[ollama_idx], display_choices[or_idx] = display_choices[or_idx], display_choices[ollama_idx]

        for i, (model_name, label, _) in enumerate(display_choices, 1):
            suffix = ""
            if "openrouter" in model_name:
                suffix = " [green]<- recommended (free)[/green]"
            console.print(f"  [cyan][{i}][/cyan] {model_name} ({label}){suffix}")
        console.print()
        console.print("  [dim]Get a free API key at https://openrouter.ai/settings/keys[/dim]")

    console.print(f"  [cyan][{len(display_choices) + 1}][/cyan] Other (enter model name)")

    choice = Prompt.ask(
        "[bold green]>[/bold green]",
        default="1",
    ).strip()

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(display_choices):
            model, _, env_var = display_choices[idx]
        else:
            model = Prompt.ask("  Enter model name").strip()
            env_var = None
    except ValueError:
        model = choice if "/" in choice or len(choice) > 3 else display_choices[0][0]
        env_var = None

    console.print()

    # 2. Auto-resume
    console.print("[bold]Auto-resume previous sessions?[/bold]")
    console.print("  [cyan][1][/cyan] Yes — always resume where I left off")
    console.print("  [cyan][2][/cyan] No — ask me each time")
    resume_choice = Prompt.ask("[bold green]>[/bold green]", default="1").strip()
    auto_resume = resume_choice != "2"

    console.print()

    # 3. API key check
    if env_var:
        if os.environ.get(env_var):
            console.print(f"  [green]✓[/green] {env_var} is set")
        else:
            console.print(f"  [yellow]✗[/yellow] {env_var} not found. Export it:")
            console.print(f'    [dim]export {env_var}="your-key-here"[/dim]')
    elif "ollama" in model:
        console.print("  [green]✓[/green] Local model — no API key needed")
    console.print()

    return {
        "project": {"name": workspace.name},
        "model": model,
        "resume": {"auto": auto_resume},
    }


def _print_startup_guidelines(config: dict) -> None:
    """Print a Getting Started panel after first-time setup."""
    model = config.get("model", "")
    lines = []

    if "groq" in model:
        lines.append("[yellow]Rate limits:[/yellow] Groq free tier allows ~30 req/min, ~14,400 req/day")
    if "openrouter" in model:
        lines.append("[yellow]Rate limits:[/yellow] OpenRouter free models have varying limits")
        lines.append("  Check limits: https://openrouter.ai/models")

    lines.append("")
    lines.append("[bold]Tips:[/bold]")
    lines.append("  Get a free API key: https://openrouter.ai/settings/keys")
    lines.append("  Don't edit .geekcode/ manually — GeekCode manages it automatically")
    lines.append("  Commit .geekcode/ to git for team collaboration")
    lines.append("")
    lines.append("[dim]Ctrl+C[/dim] interrupt  [dim]Ctrl+D[/dim] or [dim]/exit[/dim] quit  [dim]↑/↓[/dim] history  [dim]/help[/dim] commands")

    console.print(Panel(
        "\n".join(lines),
        title="Getting Started",
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()


def ensure_initialized(workspace: Path, interactive: bool = True) -> Path:
    """Ensure .geekcode/ exists. Run first-time setup if interactive."""
    geekcode_dir = workspace / ".geekcode"

    if not geekcode_dir.exists():
        import yaml

        # Create directory structure
        geekcode_dir.mkdir(parents=True)
        (geekcode_dir / "context").mkdir()
        (geekcode_dir / "cache").mkdir()
        (geekcode_dir / "history").mkdir()

        # Interactive setup or silent defaults
        if interactive and sys.stdin.isatty():
            config = _run_first_time_setup(workspace)
        else:
            config = {
                "project": {"name": workspace.name},
                "model": "claude-sonnet-4-5",
                "resume": {"auto": True},
            }

        with open(geekcode_dir / "config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        with open(geekcode_dir / "state.yaml", "w") as f:
            yaml.dump({"status": "idle"}, f)

        console.print(f"[dim]Initialized .geekcode/ in {workspace}[/dim]\n")

        if interactive and sys.stdin.isatty():
            _print_startup_guidelines(config)

    return geekcode_dir


class GeekCodeREPL:
    """
    Interactive chat interface for GeekCode.

    This REPL holds NO state. Every command:
    - Creates a fresh Agent instance
    - Agent reads from files
    - Agent writes to files
    - Agent returns result
    - REPL displays result

    No memory between commands - everything is in .geekcode/ files.
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.geekcode_dir = ensure_initialized(workspace)
        self.running = True
        self._ctrlc_count = 0
        self._input_count = 0
        self._init_readline()

    # All slash commands for tab-completion
    SLASH_COMMANDS = [
        "/help", "/?",
        "/status",
        "/history",
        "/models",
        "/model ",
        "/tools", "/tools refresh", "/tools info ",
        "/benchmark run", "/benchmark run ", "/benchmark report",
        "/loop", "/loop resume", "/loop reset",
        "/newchat",
        "/clear",
        "/reset",
        "/exit", "/quit", "/q",
    ]

    def _init_readline(self):
        """Initialize readline for arrow-key history and slash-command completion."""
        try:
            import readline
        except ImportError:
            try:
                import pyreadline3 as readline
            except ImportError:
                self._readline = None
                return
        self._readline = readline
        self._history_file = self.geekcode_dir / "input_history"
        readline.set_history_length(500)
        if self._history_file.exists():
            try:
                readline.read_history_file(str(self._history_file))
            except (OSError, IOError):
                pass

        # Set up tab-completion for slash commands
        def completer(text, state):
            if text.startswith("/"):
                matches = [c for c in self.SLASH_COMMANDS if c.startswith(text)]
            else:
                matches = []
            return matches[state] if state < len(matches) else None

        readline.set_completer(completer)
        readline.set_completer_delims("")
        readline.parse_and_bind("tab: complete")

    def _save_history(self):
        """Persist readline history to disk."""
        if self._readline is not None:
            try:
                self._readline.write_history_file(str(self._history_file))
            except (OSError, IOError):
                pass

    def _get_input(self) -> str:
        """Get user input with Rich prompt prefix and readline support."""
        console.print("[bold green]> [/bold green]", end="")
        return input().strip()

    def _create_agent(self):
        """Create a fresh agent (reads all state from files)."""
        from geekcode.core.agent import Agent
        return Agent(self.workspace)

    def _print_banner(self):
        """Print welcome banner with ASCII art."""
        ascii_art = r"""
  ██████╗ ███████╗███████╗██╗  ██╗ ██████╗ ██████╗ ██████╗ ███████╗
 ██╔════╝ ██╔════╝██╔════╝██║ ██╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
 ██║  ███╗█████╗  █████╗  █████╔╝ ██║     ██║   ██║██║  ██║█████╗
 ██║   ██║██╔══╝  ██╔══╝  ██╔═██╗ ██║     ██║   ██║██║  ██║██╔══╝
 ╚██████╔╝███████╗███████╗██║  ██╗╚██████╗╚██████╔╝██████╔╝███████╗
  ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝╚═════╝ ╚══════╝"""
        console.print(Text(ascii_art, style="bold blue"))
        console.print()
        info = Text()
        info.append(f"  v{__version__}", style="bold cyan")
        info.append("  |  ", style="dim")
        info.append(f"Workspace: {self.workspace}", style="dim")
        console.print(info)
        console.print("  [dim]Type your task, or /help for commands. /exit to quit.[/dim]")
        console.print("  [dim]Ctrl+C to interrupt, Ctrl+D or /exit to quit. Up/down arrows for history.[/dim]")
        console.print()

    def _print_goodbye(self):
        """Print farewell visual."""
        console.print()
        console.print(Panel(
            "[bold blue]Thanks for using GeekCode![/bold blue]\n"
            f"[dim]Your session is saved in .geekcode/[/dim]\n"
            "[dim]See you next time![/dim]",
            border_style="blue",
            padding=(1, 2),
        ))

    def _print_help(self):
        """Print help message."""
        help_text = """
[bold]Commands:[/bold]
  /help, /?                Show this help
  /status                  Current state, model, cache stats
  /history                 Recent task history
  /models                  List available providers and models
  /model <name>            Switch model (e.g., /model gpt-4o)
  /tools                   List MCPorter tools and token savings
  /tools refresh           Re-fetch tool manifests from MCP servers
  /tools info <name>       Show full schema for a specific tool
  /benchmark run [domain]  Run benchmarks (all or single domain)
  /benchmark report        Generate SVG charts and markdown report
  /loop                    Show coding loop status
  /loop resume             Resume interrupted coding loop
  /loop reset              Clear coding loop checkpoint
  /newchat                 Start fresh conversation (clear context)
  /clear                   Clear screen
  /reset                   Reset task state
  /exit, /quit, /q         Exit GeekCode

[bold]Usage:[/bold]
  Just type your task and press Enter.

[bold]Examples:[/bold]
  > Explain this codebase
  > What does the config file do?
  > Add tests for the user service
  > Analyze the insurance policy in docs/
"""
        console.print(Panel(help_text.strip(), title="GeekCode Help", border_style="blue"))

    def _print_status(self):
        """Print current status."""
        import yaml

        state_file = self.geekcode_dir / "state.yaml"
        config_file = self.geekcode_dir / "config.yaml"

        state = {}
        config = {}

        if state_file.exists():
            with open(state_file) as f:
                state = yaml.safe_load(f) or {}

        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f) or {}

        console.print(f"[cyan]Project:[/cyan] {config.get('project', {}).get('name', self.workspace.name)}")
        console.print(f"[cyan]Model:[/cyan] {config.get('model', 'default')}")
        console.print(f"[cyan]Status:[/cyan] {state.get('status', 'idle')}")

        if state.get('current_task'):
            console.print(f"[cyan]Task:[/cyan] {state['current_task'][:60]}...")

        # Cache stats
        from geekcode.core.cache import CacheEngine
        cache = CacheEngine(self.geekcode_dir / "cache")
        stats = cache.stats()
        console.print(f"[cyan]Cache:[/cyan] {stats['hits']} hits, ~{stats['tokens_saved_estimate']} tokens saved")

    def _print_history(self, days: int = 7):
        """Print task history."""
        import yaml
        from datetime import datetime, timedelta
        from rich.table import Table

        history_dir = self.geekcode_dir / "history"
        if not history_dir.exists():
            console.print("[dim]No history yet[/dim]")
            return

        cutoff = datetime.utcnow() - timedelta(days=days)
        entries = []

        for history_file in sorted(history_dir.glob("*.yaml"), reverse=True):
            with open(history_file) as f:
                data = yaml.safe_load(f) or []
            for entry in data:
                ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01"))
                if ts >= cutoff:
                    entries.append(entry)

        if not entries:
            console.print("[dim]No recent history[/dim]")
            return

        table = Table(show_header=True, header_style="bold")
        table.add_column("Time", style="dim", width=12)
        table.add_column("Task", style="white")
        table.add_column("", width=3)

        for entry in entries[:10]:
            table.add_row(
                entry.get("timestamp", "")[:16].replace("T", " "),
                entry.get("task", "")[:50],
                "⚡" if entry.get("cached") else "",
            )

        console.print(table)

    def _list_models(self):
        """List available providers and popular models."""
        import yaml
        from rich.table import Table

        # Read current model from config
        config_file = self.geekcode_dir / "config.yaml"
        config = {}
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f) or {}
        current = config.get("model", "")

        catalog = [
            ("openai", "OpenAI", [
                "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini",
            ]),
            ("anthropic", "Anthropic", [
                "claude-opus-4-6", "claude-sonnet-4-5-20250929",
                "claude-haiku-4-5-20251001", "claude-3-sonnet-20240229",
            ]),
            ("google", "Google", [
                "gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro",
            ]),
            ("groq", "Groq (fast)", [
                "llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                "deepseek-r1-distill-llama-70b", "gemma2-9b-it",
            ]),
            ("together", "Together AI", [
                "meta-llama/Llama-3.3-70B-Instruct-Turbo",
                "Qwen/Qwen2.5-72B-Instruct-Turbo",
                "mistralai/Mixtral-8x22B-Instruct-v0.1",
                "deepseek-ai/DeepSeek-R1",
            ]),
            ("openrouter", "OpenRouter (100+ models)", [
                "openai/gpt-4o", "anthropic/claude-sonnet-4-5",
                "google/gemini-2.0-flash-001", "deepseek/deepseek-r1",
                "meta-llama/llama-3.3-70b-instruct",
            ]),
            ("ollama", "Ollama (local)", [
                "llama3", "codellama", "mistral", "phi",
            ]),
        ]

        table = Table(title="Available Models", show_lines=True, border_style="blue")
        table.add_column("Provider", style="bold cyan", width=28)
        table.add_column("Models", style="white")

        for prefix, label, models in catalog:
            model_lines = []
            for m in models:
                display = f"{prefix}/{m}"
                if display == current or m == current:
                    model_lines.append(f"[bold green]{display} (active)[/bold green]")
                else:
                    model_lines.append(display)
            table.add_row(label, "\n".join(model_lines))

        console.print(table)
        console.print()
        console.print("[dim]Switch with: /model provider/model-name[/dim]")
        console.print("[dim]Example:     /model groq/llama-3.3-70b-versatile[/dim]")

    def _switch_model(self, model_name: str):
        """Switch to a different model."""
        import yaml

        config_file = self.geekcode_dir / "config.yaml"
        config = {}
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f) or {}

        config["model"] = model_name

        with open(config_file, "w") as f:
            yaml.dump(config, f)

        console.print(f"[green]Switched to {model_name}[/green]")

    def _reset_state(self):
        """Reset task state."""
        import yaml
        with open(self.geekcode_dir / "state.yaml", "w") as f:
            yaml.dump({"status": "idle"}, f)
        console.print("[green]State reset[/green]")

    def _new_chat(self):
        """Clear conversation and start fresh."""
        conv_file = self.geekcode_dir / "conversation.yaml"
        if conv_file.exists():
            conv_file.unlink()
        console.print("[green]Started new conversation[/green]")

    def _save_paused_state(self, task: str):
        """Save paused state so the task can be resumed later."""
        import yaml
        from datetime import datetime
        state_file = self.geekcode_dir / "state.yaml"
        state = {}
        if state_file.exists():
            with open(state_file) as f:
                state = yaml.safe_load(f) or {}
        state["status"] = "paused"
        state["paused_task"] = task
        state["paused_at"] = datetime.utcnow().isoformat()
        with open(state_file, "w") as f:
            yaml.dump(state, f, default_flow_style=False)

    def _execute_task(self, task: str):
        """Execute a user task."""
        agent = self._create_agent()
        self._ctrlc_count = 0

        # Show working indicator
        try:
            with console.status("[bold blue]Thinking...[/bold blue]", spinner="dots"):
                result = agent.run(task)
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Saving checkpoint...[/yellow]")
            self._save_paused_state(task)
            self._save_history()
            console.print("[dim]Progress saved. Use /loop resume to continue, or type a new task.[/dim]")
            return

        if result.completed:
            # Show cache info if hit
            if result.cached:
                console.print(f"[dim]⚡ Cached (saved ~{result.tokens_saved} tokens)[/dim]")

            # Render response as markdown
            console.print()
            try:
                md = Markdown(result.output)
                console.print(md)
            except:
                console.print(result.output)
            console.print()

            # Footer with stats
            console.print(f"[dim]─ {result.model} · {result.tokens_used} tokens · {result.task_id[:8]}[/dim]")
        else:
            console.print(f"[red]Error: {result.error}[/red]")

    def _handle_command(self, cmd: str) -> bool:
        """Handle a slash command. Returns True if should continue."""
        parts = cmd.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if command in ("/exit", "/quit", "/q"):
            self.running = False
            return False

        elif command in ("/help", "/?"):
            self._print_help()

        elif command == "/status":
            self._print_status()

        elif command == "/history":
            self._print_history()

        elif command == "/models":
            self._list_models()

        elif command == "/model":
            if args:
                self._switch_model(args)
            else:
                self._list_models()

        elif command == "/clear":
            console.clear()
            self._print_banner()

        elif command == "/reset":
            self._reset_state()

        elif command == "/tools":
            self._handle_tools(args)

        elif command == "/benchmark":
            self._handle_benchmark(args)

        elif command == "/loop":
            self._handle_loop(args)

        elif command == "/newchat":
            self._new_chat()

        else:
            console.print(f"[yellow]Unknown command: {command}[/yellow]")
            # Suggest closest match
            known = ["/help", "/status", "/history", "/models", "/model",
                     "/tools", "/benchmark", "/loop", "/newchat", "/clear",
                     "/reset", "/exit", "/quit"]
            close = [c for c in known if c.startswith(command[:3])]
            if close:
                console.print(f"[dim]Did you mean: {', '.join(close)}?[/dim]")
            else:
                console.print("[dim]Type /help for available commands[/dim]")

        return True

    def _handle_loop(self, args: str):
        """Handle /loop commands (coding loop status/resume/reset)."""
        from geekcode.core.coding_loop import CodingLoop

        loop = CodingLoop(self.workspace, self.geekcode_dir)
        parts = args.strip().split()
        sub = parts[0] if parts else "status"

        if sub == "status" or not args.strip():
            state = loop.get_status()
            if not state:
                console.print("[dim]No active coding loop.[/dim]")
                return

            console.print(f"[cyan]Task:[/cyan] {state.get('task', 'unknown')[:60]}")
            console.print(f"[cyan]Status:[/cyan] {state.get('status', 'unknown')}")
            console.print(f"[cyan]Iteration:[/cyan] {state.get('iteration', 0)}/{state.get('max_iterations', 5)}")

            if state.get("test_command"):
                console.print(f"[cyan]Test cmd:[/cyan] {state['test_command']}")

            for it in state.get("iterations", []):
                status = "[green]PASS[/green]" if it.get("test_passed") else "[red]FAIL[/red]"
                console.print(f"  Iteration {it['number']}: {status} ({it.get('tokens', 0):,} tokens)")

        elif sub == "resume":
            state = loop.get_status()
            if not state or state.get("status") != "running":
                console.print("[yellow]No resumable coding loop found.[/yellow]")
                return

            console.print(f"[blue]Resuming coding loop: {state.get('task', '')[:60]}...[/blue]")
            with console.status("[bold blue]Edit-test loop running...[/bold blue]", spinner="dots"):
                result = loop.resume()

            if result:
                console.print()
                try:
                    from rich.markdown import Markdown as _Md
                    console.print(_Md(result.final_output))
                except Exception:
                    console.print(result.final_output)
            else:
                console.print("[red]Resume failed.[/red]")

        elif sub == "reset":
            if loop.reset():
                console.print("[green]Coding loop checkpoint cleared.[/green]")
            else:
                console.print("[dim]No checkpoint to clear.[/dim]")

        else:
            console.print("[bold]Loop commands:[/bold]")
            console.print("  /loop              Show coding loop status")
            console.print("  /loop resume       Resume interrupted loop")
            console.print("  /loop reset        Clear loop checkpoint")

    def _handle_tools(self, args: str):
        """Handle /tools commands (MCPorter)."""
        from pathlib import Path as _Path
        parts = args.strip().split()
        sub = parts[0] if parts else "list"

        try:
            from geekcode.mcporter.registry import ToolRegistry
            registry = ToolRegistry(self.geekcode_dir)
        except Exception as e:
            console.print(f"[red]MCPorter error: {e}[/red]")
            return

        if sub == "list" or not args.strip():
            tools = registry.list_tools()
            if not tools:
                console.print("[dim]No tools available. Configure MCP servers in .geekcode/config.yaml:[/dim]")
                console.print("[dim]  mcporter:[/dim]")
                console.print("[dim]    enabled: true[/dim]")
                console.print("[dim]    servers:[/dim]")
                console.print('[dim]      playwright:[/dim]')
                console.print('[dim]        command: "npx"[/dim]')
                console.print('[dim]        args: ["@anthropic/mcp-playwright"][/dim]')
                console.print("\n[dim]Then run: /tools refresh[/dim]")
                return

            console.print(f"[bold]Available tools ({len(tools)}):[/bold]")
            for tool in tools:
                console.print(f"  [cyan]{tool.qualified_name}[/cyan] — {tool.description}")

            # Token savings
            report = registry.token_savings_report()
            if report:
                console.print()
                for server, data in report.items():
                    console.print(
                        f"  [dim]{server}: {data['tools_count']} tools, "
                        f"{data['standard_mcp_tokens']:,} → {data['mcporter_tokens']:,} tokens "
                        f"({data['savings_pct']} saved)[/dim]"
                    )

        elif sub == "refresh":
            import yaml as _yaml
            config_file = self.geekcode_dir / "config.yaml"
            config = {}
            if config_file.exists():
                with open(config_file) as f:
                    config = _yaml.safe_load(f) or {}

            mcporter_cfg = config.get("mcporter", {})
            if not mcporter_cfg.get("enabled"):
                console.print("[yellow]MCPorter is disabled. Set mcporter.enabled: true in config.yaml[/yellow]")
                return

            servers = mcporter_cfg.get("servers", {})
            if not servers:
                console.print("[yellow]No servers configured in mcporter.servers[/yellow]")
                return

            for name, srv_cfg in servers.items():
                if not srv_cfg.get("enabled", True):
                    continue
                console.print(f"[blue]Refreshing {name}...[/blue]")
                try:
                    manifest = registry.refresh(server_config=srv_cfg, server_name=name)
                    console.print(
                        f"  [green]{len(manifest.tools)} tools fetched "
                        f"({manifest.full_schema_tokens:,} → {manifest.mcporter_tokens:,} tokens)[/green]"
                    )
                except Exception as e:
                    console.print(f"  [red]Failed: {e}[/red]")

        elif sub == "info":
            tool_name = parts[1] if len(parts) > 1 else ""
            if not tool_name:
                console.print("[yellow]Usage: /tools info <server.tool_name>[/yellow]")
                return
            schema = registry.build_full_schema(tool_name)
            console.print(schema)

        else:
            console.print("[bold]Tool commands:[/bold]")
            console.print("  /tools              List available MCP tools")
            console.print("  /tools refresh      Re-fetch manifests from MCP servers")
            console.print("  /tools info <name>  Show full schema for a tool")

    def _handle_benchmark(self, args: str):
        """Handle /benchmark commands."""
        from pathlib import Path as _Path

        parts = args.strip().split()
        sub = parts[0] if parts else "help"

        if sub == "run":
            domain = parts[1] if len(parts) > 1 else None
            try:
                from benchmarks.runner import BenchmarkRunner
                runner = BenchmarkRunner()
                label = domain or "all domains"
                console.print(f"[bold blue]Running benchmarks for {label}...[/bold blue]")
                with console.status("[bold blue]Benchmarking...[/bold blue]", spinner="dots"):
                    if domain:
                        results = runner.run_domain(domain)
                    else:
                        results = runner.run_all()
                for r in results:
                    status = "[green]OK[/green]" if r.completed else f"[red]FAIL[/red] ({r.error})"
                    console.print(f"  {r.domain}/task{r.task_id} — {status}")
                console.print(f"\n[green]{len(results)} tasks completed.[/green]")
            except Exception as e:
                console.print(f"[red]Benchmark error: {e}[/red]")

        elif sub == "report":
            try:
                from benchmarks.evaluate import Evaluator
                from benchmarks.report import ReportGenerator
                console.print("[bold blue]Generating report...[/bold blue]")
                evaluator = Evaluator()
                scorecards = evaluator.compare_agents()
                gen = ReportGenerator(scorecards)
                out_dir = _Path(__file__).resolve().parent.parent.parent / "docs" / "benchmarks"
                gen.save_svgs(out_dir)
                gen.save_report(out_dir / "report.md")
                console.print(f"[green]Report saved to {out_dir}[/green]")
                console.print(f"[dim]  radar_chart.svg, bar_chart.svg, latency_chart.svg, token_chart.svg[/dim]")
                console.print(f"[dim]  report.md[/dim]")
                # Show summary table
                console.print()
                console.print(gen.overall_comparison_table())
            except Exception as e:
                console.print(f"[red]Report error: {e}[/red]")

        else:
            console.print("[bold]Benchmark commands:[/bold]")
            console.print("  /benchmark run            Run all domains")
            console.print("  /benchmark run <domain>   Run a single domain (coding, finance, healthcare, general)")
            console.print("  /benchmark report         Generate SVG charts and markdown report")

    def run(self):
        """Run the interactive REPL."""
        self._print_banner()

        while self.running:
            try:
                # Get user input (with readline arrow-key history)
                user_input = self._get_input()
                self._ctrlc_count = 0

                if not user_input:
                    continue

                self._input_count += 1
                if self._input_count % 5 == 0:
                    self._save_history()

                # Handle commands
                if user_input.startswith("/"):
                    if not self._handle_command(user_input):
                        break
                    continue

                # Intercept exit keywords before sending to LLM
                EXIT_KEYWORDS = {"quit", "exit", "close", "bye", "goodbye", "q"}
                if user_input.lower().strip() in EXIT_KEYWORDS:
                    break

                # Execute as task
                self._execute_task(user_input)
                console.print()

            except EOFError:
                # Ctrl+D
                self._save_history()
                break
            except KeyboardInterrupt:
                self._ctrlc_count += 1
                if self._ctrlc_count >= 2:
                    console.print("\n[dim]Saving and exiting...[/dim]")
                    self._save_history()
                    break
                console.print("\n[dim]Press Ctrl+C again to exit, or type a command.[/dim]")
                continue
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        self._save_history()
        self._print_goodbye()


def _is_project_directory(path: Path) -> bool:
    """Check if path looks like a project/workspace directory."""
    project_markers = [
        ".git", ".svn", ".hg",                    # VCS
        "package.json", "pyproject.toml",          # Package configs
        "Cargo.toml", "go.mod", "pom.xml",         # Language projects
        "Makefile", "CMakeLists.txt",              # Build systems
        ".geekcode",                                # Already initialized
        "requirements.txt", "setup.py", "setup.cfg",
        "Gemfile", "build.gradle", "build.sbt",
        ".project", ".idea", ".vscode",            # IDEs
        "docker-compose.yml", "Dockerfile",
    ]
    return any((path / marker).exists() for marker in project_markers)


def _find_project_root() -> Optional[Path]:
    """Walk up from cwd looking for a project marker. Returns None if none found."""
    current = Path.cwd()
    while current != current.parent:
        if _is_project_directory(current):
            return current
        current = current.parent
    return None


@click.command()
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.option("--init", "-i", is_flag=True, help="Initialize and exit")
@click.argument("task", required=False, nargs=-1)
def cli(version: bool, init: bool, task: tuple) -> None:
    """
    GeekCode - AI agent for knowledge work.

    Run without arguments to start interactive mode.

    \b
    Examples:
        geekcode                    # Start interactive chat
        geekcode "explain this"     # Run single task
        geekcode --init             # Initialize only
    """
    if version:
        console.print(f"GeekCode v{__version__}")
        return

    workspace = find_workspace()

    # Reject running at root/home with no project markers
    if not _is_project_directory(workspace):
        project_root = _find_project_root()
        if project_root:
            workspace = project_root
        else:
            console.print("[red]Error: Not inside a project directory.[/red]")
            console.print(
                "[dim]Navigate to a project folder (with .git, package.json, etc.) "
                "and try again.[/dim]"
            )
            sys.exit(1)

    if init:
        ensure_initialized(workspace)
        console.print(f"[green]Initialized .geekcode/ in {workspace}[/green]")
        return

    # If task provided as argument, run it directly (no interactive setup)
    if task:
        task_str = " ".join(task)
        ensure_initialized(workspace, interactive=False)

        from geekcode.core.agent import Agent
        agent = Agent(workspace)

        with console.status("[bold blue]Working...[/bold blue]"):
            result = agent.run(task_str)

        if result.completed:
            if result.cached:
                console.print(f"[dim]⚡ Cached[/dim]")
            console.print(result.output)
        else:
            console.print(f"[red]Error: {result.error}[/red]")
            sys.exit(1)
        return

    # Interactive mode
    repl = GeekCodeREPL(workspace)
    repl.run()


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
