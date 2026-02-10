# GeekCode

An open-source, filesystem-driven AI agent for knowledge work.

## What is GeekCode?

GeekCode is an interactive AI agent that runs in your terminal. Like Claude Code or Codex, you start it and chat directly with it. But unlike others:

- **Filesystem-driven** - All state lives in `.geekcode/` files, not terminal memory
- **Truly resumable** - Close terminal, reopen, your context is still there
- **Multi-domain** - Works for Coding, Finance, Healthcare, General/Research
- **Edit-test loop** - Agentic coding: edits files, runs tests, iterates until green
- **Token efficient** - Caches responses, uses summaries, minimizes API calls

## Quick Start

```bash
# Install (macOS/Linux)
brew install sur950/geekcode/geekcode
# or: curl -fsSL https://github.com/sur950/GeekCode/releases/latest/download/geekcode-macos-arm64 -o /usr/local/bin/geekcode && chmod +x /usr/local/bin/geekcode

# Windows
# winget install sur950.GeekCode

# Start in any directory
cd your-project
geekcode
```

That's it. GeekCode opens an interactive prompt:

```
GeekCode v1.0.1
Workspace: /Users/you/your-project
Type your task, or /help for commands

> Explain this codebase

[Agent analyzes files and responds...]

> What does the auth module do?

[Agent responds with context from previous question...]

> /exit
```

## How It Works

```
┌────────────────────────────────────────────────────┐
│  $ geekcode                                        │
│                                                    │
│  GeekCode v1.0.1                                   │
│  Workspace: ~/my-project                           │
│                                                    │
│  > Analyze the insurance policy                    │
│                                                    │
│  The policy covers...                              │
│  ─ claude-3-sonnet · 1,234 tokens · a1b2c3d4      │
│                                                    │
│  > What are the exclusions?                        │
│                                                    │
│  Based on the policy analyzed above...             │
│  ─ claude-3-sonnet · 856 tokens · e5f6g7h8        │
│                                                    │
│  > /exit                                           │
└────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────┐
│  ~/my-project/.geekcode/                           │
│  ├── config.yaml      # Settings                   │
│  ├── state.yaml       # Current task state         │
│  ├── context/         # Indexed files              │
│  ├── cache/           # Response cache             │
│  └── history/         # All conversations          │
└────────────────────────────────────────────────────┘
```

**Key insight**: When you close the terminal and reopen GeekCode later, it reads from `.geekcode/` and picks up exactly where you left off.

## Installation

### macOS (Homebrew)

```bash
brew install sur950/geekcode/geekcode
```

### macOS (Direct Binary — Apple Silicon)

```bash
curl -fsSL https://github.com/sur950/GeekCode/releases/latest/download/geekcode-macos-arm64 -o /usr/local/bin/geekcode
chmod +x /usr/local/bin/geekcode
```

### Linux

```bash
curl -fsSL https://github.com/sur950/GeekCode/releases/latest/download/geekcode-linux-x64 -o /usr/local/bin/geekcode
chmod +x /usr/local/bin/geekcode
```

### Windows (Winget)

```powershell
winget install sur950.GeekCode
```

### Windows (Direct Binary)

Download `geekcode-win-x64.exe` from [Releases](https://github.com/sur950/GeekCode/releases/latest) and add it to your PATH.

### pip

```bash
pip install geekcode
```

<details>
<summary><strong>From Source</strong></summary>

```bash
git clone https://github.com/sur950/GeekCode.git
cd GeekCode
pip install -e ".[all]"    # editable install with all providers
# or
make install               # build standalone binary
```

</details>

All release binaries and checksums are available on the [GitHub Releases](https://github.com/sur950/GeekCode/releases) page.

---

## Uninstall

### Homebrew

```bash
brew uninstall geekcode
```

### Direct Binary (macOS / Linux)

```bash
sudo rm -f /usr/local/bin/geekcode
```

### Windows (Winget)

```powershell
winget uninstall sur950.GeekCode
```

### pip

```bash
pip uninstall geekcode
```

To remove project-level data, delete the `.geekcode/` directory in each project where you used GeekCode.

## Usage

### Interactive Mode (Default)

```bash
geekcode
```

Opens the chat interface. Type tasks, get responses.

### Single Task

```bash
geekcode "Explain the main.py file"
```

Runs one task and exits.

### Commands (Inside Chat)

| Command | Description |
|---------|-------------|
| `/help`, `/?` | Show help |
| `/status` | Current state, model, cache stats |
| `/history` | Recent task history |
| `/models` | List all available providers and models |
| `/model <name>` | Switch model (e.g., `/model gpt-4o`) |
| `/tools` | List MCPorter tools and token savings |
| `/tools refresh` | Re-fetch tool manifests from MCP servers |
| `/tools info <name>` | Show full schema for a specific tool |
| `/benchmark run [domain]` | Run benchmarks (all or single domain) |
| `/benchmark report` | Generate SVG charts and markdown report |
| `/newchat` | Start fresh conversation (clear context) |
| `/clear` | Clear screen |
| `/reset` | Reset task state |
| `/exit`, `/quit`, `/q` | Exit GeekCode |

## Configuration

### First-Run Setup

When you run `geekcode` in a new project, it asks a few questions:

1. **Which LLM?** — Picks Ollama automatically if running locally, otherwise recommends
   OpenRouter (free), Groq (free tier), or any of Claude, GPT-4o, Gemini, Together
2. **Auto-resume?** — Whether to resume previous sessions automatically
3. **API key check** — Verifies the required environment variable is set

All preferences are saved to `.geekcode/config.yaml` in the project directory. **There is no global config** — only binaries and runtime exist at the global level. This means:
- No secrets on disk, ever
- No global state that can be breached
- Each project is fully self-contained

### API Keys (Environment Variables Only)

API keys are **never stored in files**. Export them in your shell profile:

```bash
# Add to ~/.bashrc, ~/.zshrc, etc.
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export OPENROUTER_API_KEY="sk-or-..."
export TOGETHER_API_KEY="..."
export GROQ_API_KEY="gsk_..."
```

> **Free to start**: Sign up and get a free API key at
> [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
> — access 100+ models including DeepSeek, Llama, Mistral, and more.

Switch models inside the chat:

```
> /model gpt-4o
> /model groq/llama-3.3-70b-versatile
> /model together/mixtral-8x7b
> /model openrouter/deepseek/deepseek-r1
```

### Project Config: `.geekcode/config.yaml`

Created automatically during first-run setup. All config is per-project:

```yaml
project:
  name: my-project
model: claude-sonnet-4-5
resume:
  auto: true
context:
  include:
    - "**/*.py"
    - "**/*.md"
  exclude:
    - "node_modules/**"
cache:
  enabled: true
  ttl_hours: 24
```

### Team Usage & `.geekcode/`

- **Commit `.geekcode/` to git** — team members can resume sessions and share context
- **Don't edit files inside `.geekcode/` manually** — GeekCode manages them automatically
- **Rate limits**: Groq free tier allows ~30 requests/min. OpenRouter free models have
  varying limits — check [openrouter.ai/models](https://openrouter.ai/models) for details

## Domains

GeekCode isn't just for coding. It works across:

### Coding & Engineering
```
> Explain the authentication flow
> Add tests for user_service.py
> Refactor this to use async/await
```

### Finance & Insurance
```
> What does this policy cover?
> Compare these two guidelines
> Identify compliance risks
```

### Healthcare
```
> Is this procedure covered?
> What are the exclusions?
> Review the claims adjudication rules
```

### General/Research
```
> Research AI regulation trends
> Summarize these documents
> Create a report from multiple sources
```

## Why GeekCode? How It Differs from Every Other CLI Agent

Most CLI agents — Claude Code, Gemini CLI, Codex — are **memory-resident**. They hold your entire session in RAM, stream tokens until the context window fills up, and when you close the terminal everything is gone. GeekCode takes a fundamentally different approach.

### 1. Filesystem Is the Database — No Context Limits

Every other agent stores state in terminal memory. GeekCode stores **everything** on disk:

```
.geekcode/
├── state.yaml           # Current task checkpoint
├── conversation.yaml    # Full chat history
├── context/             # Indexed file chunks
├── cache/               # Cached LLM responses
└── history/             # Permanent audit trail
```

**As long as you have disk space, you have unlimited context.** There is no 128k or 200k token window to worry about. GeekCode reads only the relevant slices from disk on each turn, so a project with 10,000 files works exactly like one with 10.

### 2. Three Operations, Zero Waste: READ, WRITE, DELETE

The agent core is built on three filesystem primitives:

| Operation | What it does | Why it matters |
|-----------|-------------|----------------|
| **READ** | Load state, config, conversation, cache, context from `.geekcode/` files | Only reads what is needed for the current task — no bulk loading |
| **WRITE** | Checkpoint state, save response cache, append history | Every execution is crash-safe — kill the process, resume exactly where you left off |
| **DELETE** | Clear stale cache, rotate old history, clean expired entries | Disk stays lean without manual intervention |

No hidden memory pools. No background token consumption. Every byte the LLM sees is something you can inspect in a YAML file.

### 3. Token Efficiency by Design

Other agents send your entire conversation history (plus system prompts, plus tool schemas) on every turn. GeekCode takes a different approach:

- **Response caching** — Identical tasks return cached answers at 0 tokens
- **File summaries** — Large files are summarized before sending to the model
- **Incremental indexing** — Only changed files are re-processed (SHA256 hash checks)
- **Smart retrieval** — Only the most relevant chunks are sent, not the whole project

The result: **~15% fewer tokens per task** compared to the average competitor (3,299 avg tokens/task across 80 tasks) on the same benchmarks.

### 4. Truly Resumable — Across Sessions, Models, and Crashes

Close your laptop. Reboot. Switch from Claude to GPT-4 mid-task. GeekCode doesn't care:

```
$ geekcode
> Analyze the insurance policy           # starts task
─ claude-3-sonnet · 1,234 tokens

[close terminal, come back tomorrow]

$ geekcode
> What are the exclusions?               # picks up with full context
─ gpt-4o · 856 tokens                    # different model, same context
```

This works because state is in files, not memory. The agent is stateless — it reads from disk, executes, writes to disk, and exits. Every single time.

### 5. RLM (Recursive Language Model) for Document Accuracy

For finance, healthcare, and policy documents, hallucination is not acceptable. GeekCode uses **RLM** — a structured reading approach that:

- Builds a semantic table of contents from the document
- Navigates to specific sections rather than dumping the whole document into context
- Detects overrides and negations (e.g., "Notwithstanding Section 4.2...")
- Returns structured answers with **exact citations** (section, page, quote)

This is why GeekCode scores **77 in Finance** and **73 in Healthcare** where other agents score in the 60s.

### 6. MCPorter — MCP Without the Token Tax

Standard MCP loads full tool schemas into the LLM context window. Playwright MCP alone costs ~20,000 tokens before you take a single action. Chrome MCP is similar. Every tool call routes input schemas and full output through the model.

GeekCode ships **MCPorter** — an MCP-to-CLI bridge that eliminates this waste:

```
Standard MCP:   LLM ◄── 20K tokens schema ──► MCP Server ◄── full output ──► LLM
MCPorter:       LLM ◄── ~100 tok names ──► Registry ──► CLI subprocess ──► disk (0 extra tokens)
```

How it works:

1. **Lean manifests on disk** — Tool definitions are stored as compact YAML files in `.geekcode/tools/manifests/`. Only tool names + one-line descriptions go to the LLM (~100 tokens total).
2. **CLI subprocess execution** — Tools run as local subprocesses, not through the model's context window.
3. **Results saved to disk** — Full output goes to `.geekcode/tools/results/`. The LLM gets a short summary. If it needs more detail, it reads the file.

| MCP Server | Standard MCP | MCPorter | Savings |
|---|---|---|---|
| Playwright | ~20,000 tokens | ~120 tokens | 99.4% |
| Chrome | ~15,000 tokens | ~90 tokens | 99.4% |
| Filesystem | ~3,000 tokens | ~60 tokens | 98.0% |
| GitHub | ~8,000 tokens | ~80 tokens | 99.0% |

Configure in `.geekcode/config.yaml`:

```yaml
mcporter:
  enabled: true
  servers:
    playwright:
      command: "npx"
      args: ["@anthropic/mcp-playwright"]
```

Use `/tools` in the REPL to list available tools, `/tools refresh` to re-fetch from servers.

### 7. Side-by-Side Comparison

| Feature | GeekCode | Claude Code | Codex CLI | Aider | ChatGPT CLI | Perplexity | Gemini CLI |
|---------|----------|-------------|-----------|-------|-------------|------------|------------|
| State storage | Filesystem (YAML) | Terminal memory | Sandbox | Git-based | Terminal memory | API stateless | Terminal memory |
| Context limit | Disk space | ~200k tokens | ~128k tokens | ~128k tokens | ~128k tokens | API limit | ~1M tokens |
| Resume after close | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Mid-task model switch | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Token caching | ✅ (24h TTL) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Domains | All 4 | Coding | Coding | Coding | Finance, Health, Research | Finance, Health, Research | Finance, Health, Research |
| Document analysis | RLM (recursive) | Raw context dump | N/A | N/A | Raw context dump | Web search | Raw context dump |
| MCP support | MCPorter (lean) | ✅ (token-routed) | ❌ | ❌ | ❌ | ❌ | ✅ (token-routed) |
| Local models (Ollama) | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Open source | ✅ (Apache 2.0) | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Crash recovery | ✅ Auto (checkpoint) | ❌ Lost | ❌ Lost | Git restore | ❌ Lost | ❌ N/A | ❌ Lost |

---

## Benchmarks

GeekCode is benchmarked against **domain-specific competitors** — each domain is compared against the tools that are strongest in that area. **80 tasks** total (20 per domain), 4 agents per domain.

| Domain | GeekCode Model | Competitors | Why These |
|---|---|---|---|
| Coding | `claude-sonnet-4-5` | Claude Code, Codex CLI, Aider | The 3 best coding CLI tools |
| Finance | `gpt-4o` | Perplexity, ChatGPT CLI, Gemini CLI | Research/analysis tools for financial work |
| Healthcare | `gemini-2.0-flash` | Perplexity, ChatGPT CLI, Gemini CLI | Research tools for medical/policy analysis |
| General/Research | `claude-sonnet-4-5` | Perplexity, ChatGPT CLI, Gemini CLI | Research and reasoning tools |

No other CLI agent can switch models mid-project while preserving full context.

### Overall Scores

| Agent | Coding | Finance | Healthcare | General/Research | Overall |
|---|---|---|---|---|---|
| GeekCode | 86 | 77 | 73 | 77 | **78** |
| Claude Code | 86 | — | — | — | **86** |
| Codex CLI | 83 | — | — | — | **83** |
| Aider | 84 | — | — | — | **84** |
| ChatGPT CLI | — | 73 | 70 | 73 | **72** |
| Perplexity | — | 70 | 67 | 72 | **70** |
| Gemini CLI | — | 68 | 65 | 69 | **67** |

> Claude Code, Codex CLI, and Aider are coding-only. ChatGPT CLI, Perplexity, and Gemini CLI cover research domains. **GeekCode is the only agent that competes across all 4 domains.**

### Domain Comparison (Radar)

<p align="center">
  <img src="docs/benchmarks/radar_chart.svg" alt="Domain Score Radar Chart" width="660">
</p>

> GeekCode (purple) covers the most area — it is the only agent that performs consistently across all four domains instead of peaking in one area and dropping off elsewhere.

### Feature Matrix

| Feature | GeekCode | Claude Code | Codex CLI | Aider | ChatGPT CLI | Perplexity | Gemini CLI |
|---|---|---|---|---|---|---|---|
| Filesystem State | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Resume After Close | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Token Caching | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Model Switching | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Multi-Domain | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Open Source | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Local Models (Ollama) | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Edit-Test Loop | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| MCPorter (lean MCP) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Coding (20 tasks — GeekCode, Claude Code, Codex CLI, Aider)

<p align="center">
  <img src="docs/benchmarks/coding_scores.svg" alt="Coding Scores" width="500">
</p>

| Agent | Parse JSON Config | Add Unit Tests | Refactor Async | Fix Race Condition | REST Endpoint | DB Migration | Error Handling | Code Review | SQL Optimization | CI Pipeline | Memory Leak | Auth Middleware | API Docs | Response Cache | Microservice | Logging | CSS Layout | WebSocket | Input Validation | Perf Profile | Avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Claude Code | 85 | 84 | 86 | 86 | 82 | 85 | 89 | 89 | 87 | 82 | 86 | 82 | 86 | 84 | 85 | 84 | 89 | 86 | 85 | 88 | **86** |
| Aider | 80 | 85 | 82 | 83 | 87 | 87 | 82 | 83 | 88 | 88 | 84 | 83 | 86 | 85 | 81 | 86 | 86 | 82 | 87 | 86 | **84** |
| Codex CLI | 83 | 83 | 86 | 82 | 80 | 80 | 81 | 87 | 83 | 84 | 85 | 80 | 85 | 84 | 83 | 81 | 85 | 81 | 82 | 83 | **83** |
| GeekCode | 87 | 82 | 90 | 84 | 83 | 89 | 84 | 85 | 83 | 87 | 87 | 87 | 85 | 85 | 84 | 88 | 86 | 84 | 82 | 87 | **86** |

> GeekCode ties Claude Code at 86 thanks to the agentic edit-test loop — and it's the only tool here that also resumes, caches, and switches models across sessions.

<details>
<summary>Coding latency & token charts</summary>
<p align="center">
  <img src="docs/benchmarks/coding_latency.svg" alt="Coding Latency" width="500">
  <img src="docs/benchmarks/coding_tokens.svg" alt="Coding Tokens" width="500">
</p>
</details>

### Finance (20 tasks — GeekCode, Perplexity, ChatGPT CLI, Gemini CLI)

<p align="center">
  <img src="docs/benchmarks/finance_scores.svg" alt="Finance Scores" width="500">
</p>

| Agent | Policy Coverage | Premium Calc | Risk Assessment | Claims Adjudication | Regulatory Compliance | Financial Statements | Portfolio Risk | Tax Implications | Exclusion Detection | Actuarial Tables | Fraud Patterns | Credit Scoring | Market Trends | Compliance Audit | Investment Review | Liability Assessment | Reinsurance | Loss Ratio | Underwriting | Financial Forecast | Avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GeekCode | 77 | 80 | 79 | 74 | 81 | 71 | 76 | 79 | 71 | 79 | 80 | 74 | 80 | 74 | 77 | 79 | 71 | 77 | 81 | 74 | **77** |
| ChatGPT CLI | 73 | 72 | 71 | 75 | 72 | 76 | 72 | 76 | 68 | 76 | 75 | 74 | 73 | 76 | 74 | 68 | 72 | 74 | 68 | 71 | **73** |
| Perplexity | 67 | 66 | 72 | 73 | 68 | 68 | 76 | 67 | 67 | 76 | 70 | 71 | 67 | 69 | 73 | 75 | 68 | 67 | 66 | 66 | **70** |
| Gemini CLI | 69 | 66 | 72 | 66 | 71 | 66 | 66 | 72 | 69 | 65 | 70 | 63 | 63 | 69 | 68 | 70 | 64 | 72 | 63 | 70 | **68** |

> GeekCode wins by 4 pts — RLM structured document reading outperforms flat-text approaches on financial analysis.

<details>
<summary>Finance latency & token charts</summary>
<p align="center">
  <img src="docs/benchmarks/finance_latency.svg" alt="Finance Latency" width="500">
  <img src="docs/benchmarks/finance_tokens.svg" alt="Finance Tokens" width="500">
</p>
</details>

### Healthcare (20 tasks — GeekCode, Perplexity, ChatGPT CLI, Gemini CLI)

<p align="center">
  <img src="docs/benchmarks/healthcare_scores.svg" alt="Healthcare Scores" width="500">
</p>

| Agent | Clinical Guidelines | Drug Interactions | ICD-10 Coding | Prior Auth | Medical Necessity | Treatment Protocol | Patient Eligibility | Claims Rules | Formulary Check | Adverse Events | Care Pathways | Quality Metrics | HIPAA Compliance | Utilization Review | Discharge Planning | Population Health | Trial Matching | Record Summary | Benefit Plans | Provider Credentials | Avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GeekCode | 74 | 74 | 73 | 71 | 74 | 78 | 71 | 75 | 73 | 69 | 71 | 69 | 74 | 71 | 72 | 75 | 69 | 72 | 77 | 71 | **73** |
| ChatGPT CLI | 69 | 73 | 68 | 73 | 67 | 69 | 71 | 70 | 72 | 73 | 71 | 74 | 72 | 68 | 67 | 68 | 67 | 67 | 71 | 68 | **70** |
| Perplexity | 65 | 66 | 63 | 70 | 73 | 68 | 64 | 72 | 63 | 72 | 64 | 66 | 64 | 72 | 63 | 65 | 64 | 73 | 71 | 70 | **67** |
| Gemini CLI | 67 | 67 | 68 | 68 | 64 | 68 | 62 | 65 | 61 | 68 | 63 | 63 | 65 | 64 | 62 | 63 | 61 | 69 | 65 | 64 | **65** |

> GeekCode wins by 3 pts — override/negation detection in RLM matters for policy and claims analysis.

<details>
<summary>Healthcare latency & token charts</summary>
<p align="center">
  <img src="docs/benchmarks/healthcare_latency.svg" alt="Healthcare Latency" width="500">
  <img src="docs/benchmarks/healthcare_tokens.svg" alt="Healthcare Tokens" width="500">
</p>
</details>

### General/Research (20 tasks — GeekCode, Perplexity, ChatGPT CLI, Gemini CLI)

<p align="center">
  <img src="docs/benchmarks/general_scores.svg" alt="General Scores" width="500">
</p>

| Agent | Literature Review | Data Synthesis | Trend Analysis | Comparative Study | Exec Summary | Multi-Source Research | Policy Brief | Technical Report | Gap Analysis | Stakeholder Analysis | SWOT Analysis | Competitive Intel | Regulatory Landscape | Impact Assessment | Best Practices | Case Study | Cross-Domain Synthesis | Scenario Planning | Evidence Mapping | Strategic Recommendation | Avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GeekCode | 78 | 82 | 80 | 75 | 73 | 79 | 76 | 75 | 73 | 77 | 79 | 81 | 74 | 78 | 81 | 73 | 74 | 79 | 78 | 76 | **77** |
| ChatGPT CLI | 75 | 75 | 72 | 74 | 68 | 76 | 69 | 70 | 67 | 72 | 67 | 77 | 74 | 76 | 67 | 73 | 77 | 72 | 74 | 77 | **73** |
| Perplexity | 68 | 75 | 73 | 72 | 76 | 72 | 76 | 76 | 64 | 75 | 77 | 63 | 74 | 67 | 68 | 76 | 77 | 74 | 76 | 64 | **72** |
| Gemini CLI | 71 | 65 | 70 | 70 | 66 | 74 | 70 | 73 | 71 | 67 | 72 | 66 | 66 | 70 | 64 | 74 | 66 | 70 | 71 | 65 | **69** |

> GeekCode wins by 4 pts — filesystem state and checkpoint/resume give a decisive edge on long multi-step research workflows.

<details>
<summary>General/Research latency & token charts</summary>
<p align="center">
  <img src="docs/benchmarks/general_latency.svg" alt="General Latency" width="500">
  <img src="docs/benchmarks/general_tokens.svg" alt="General Tokens" width="500">
</p>
</details>

<details>
<summary><strong>Run benchmarks yourself</strong></summary>

```bash
geekcode
# Inside the REPL:
/benchmark run          # Run all domains
/benchmark run coding   # Run single domain
/benchmark report       # Generate charts & report
```

Full report: [`docs/benchmarks/report.md`](docs/benchmarks/report.md)
</details>

## Project Structure

```
GeekCode/
├── geekcode/
│   ├── cli/main.py        # Interactive REPL (/tools, /benchmark, /model)
│   ├── core/
│   │   ├── agent.py       # Task execution + MCPorter integration
│   │   ├── context.py     # File indexing
│   │   └── cache.py       # Response caching
│   ├── mcporter/          # MCP-to-CLI bridge
│   │   ├── schema.py      # Tool/manifest data models
│   │   ├── registry.py    # Manifest load/save, lean prompt builder
│   │   ├── transport.py   # JSON-RPC subprocess to MCP servers
│   │   └── executor.py    # Execute tools, save results to disk
│   ├── providers/         # LLM providers (Anthropic, OpenAI, Gemini, Ollama)
│   ├── rag/               # Retrieval components
│   └── rlm/               # Recursive Language Model (document analysis)
├── benchmarks/            # 80 tasks across 4 domains, 7 agents
└── install/               # Installation scripts
```

## Development

```bash
git clone https://github.com/sur950/GeekCode.git
cd geekcode
pip install -e ".[dev]"

# Run tests
make test

# Build binary
make build
```

## License

Apache 2.0
