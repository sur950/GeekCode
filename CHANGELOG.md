# Changelog

All notable changes to GeekCode will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [1.0.7] - 2026-02-12

### Fixed
- `ContextEngine.clear()` crashed with `AttributeError` — referenced non-existent `self.index_file` instead of `self._index_path`
- `ContextEngine` was dead code — `add_file()` existed but was never called, leaving `.geekcode/context/chunks/` always empty
- Generic questions like "how does auth work?" returned zero project context because `gather_workspace_context()` only triggered on specific regex patterns

### Added
- **Always-on project summary** — every prompt now includes the file tree, README snippet (first 80 lines), and detected tech stack, so the model understands the project without regex-matched queries
- `build_project_summary()` in `workspace_query.py` — cached baseline context with hash-based invalidation
- **Auto-indexing** — workspace files are incrementally indexed on every task run (60-second cooldown), populating chunks for keyword search
- `index_workspace()` method on `ContextEngine` — walks project files and indexes up to 500 files incrementally
- `/reindex` slash command — force re-index of workspace files with autocomplete support
- First-run indexing — `.geekcode/` initialization now indexes workspace files with progress output
- Tech stack detection for 13+ ecosystems: Node.js, Python, Go, Rust, Java/Kotlin, Ruby, PHP, Dart/Flutter, Elixir, .NET — with dependency extraction from config files

### Changed
- `_build_context_from_files()` now always prepends project overview before live workspace data and chunk search
- System prompt updated to tell the model it has full project access and should reference specific files/paths
- Chunk search now returns top 5 results (was 3)

## [1.0.6] - 2026-02-11

### Fixed
- `/models` now queries Ollama for actually installed local models instead of showing a hardcoded list
- `/model <name>` no longer silently routes to the wrong provider — ambiguous model names now require explicit `provider/model` format
- Provider inference (`_infer_provider`) raises clear error for ambiguous model names (llama, qwen, mixtral, etc.) instead of guessing wrong

### Added
- Real-time command suggestions via `prompt_toolkit` — dropdown appears as you type `/` with descriptions for each command
- Model name autocompletion after `/model ` — shows dynamic Ollama models and static catalog, all in `provider/model` format
- `prompt_toolkit` added as a core dependency
- `CHANGELOG.md` — release notes now sourced from changelog instead of hardcoded in CI

### Changed
- Replaced `readline` tab-completion with `prompt_toolkit` `PromptSession` for the interactive REPL
- One-time automatic migration of readline history file to prompt_toolkit format
- GitHub Actions release workflow reads "What's Changed" from CHANGELOG.md

## [1.0.5] - 2026-01-21

### Fixed
- Multi-language workspace queries now work correctly
- Large file safety guards prevent memory issues on big files

## [1.0.4] - 2025-12-19

### Added
- Workspace query layer for git status, file listing, docs, and symbol extraction

## [1.0.3] - 2025-12-18

### Fixed
- `AgentConfig` missing `timeout` field
- API key maps added for all providers

## [1.0.2] - 2025-12-17

### Fixed
- Homebrew formula dependency resolution
- Slash-command tab completion

### Changed
- CI now syncs formula to homebrew-geekcode tap repo on release

## [1.0.1] - 2025-11-16

### Added
- Ollama auto-detection on first run
- Readline history (arrow keys recall previous inputs)
- Ctrl+C interrupt handling with graceful save
- Startup guidelines panel after first-time setup

## [1.0.0] - 2025-11-15

### Added
- Initial release — filesystem-driven AI agent for knowledge work
- Interactive REPL with slash commands (`/help`, `/models`, `/model`, `/status`, `/history`, etc.)
- Provider support: OpenAI, Anthropic, Google, Ollama, OpenRouter, Together AI, Groq
- PyInstaller binary builds for macOS ARM64, Linux x64, Windows x64
- Homebrew formula with automatic tap updates
- MCPorter tool integration (MCP-to-CLI bridge)
- Benchmark suite (80 tasks across coding, finance, healthcare, general domains)
- Coding loop (edit-test-iterate) with checkpoint/resume
- Response caching with token savings tracking
- File context indexing and chunking
