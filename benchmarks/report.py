"""Report generator — markdown tables and pure-Python SVG charts."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

from benchmarks.models import ALL_AGENTS, DOMAIN_AGENTS, DOMAIN_LABELS, DOMAINS, TASK_NAMES, AgentScorecard

# ── Colour palette per agent ────────────────────────────────────────────────

AGENT_COLOURS: Dict[str, str] = {
    "geekcode": "#6C63FF",
    "claude_code": "#D97706",
    "codex_cli": "#0EA5E9",
    "aider": "#DC2626",
    "chatgpt_cli": "#10B981",
    "perplexity": "#7C3AED",
    "gemini_cli": "#F59E0B",
}

AGENT_LABELS: Dict[str, str] = {
    "geekcode": "GeekCode",
    "claude_code": "Claude Code",
    "codex_cli": "Codex CLI",
    "aider": "Aider",
    "chatgpt_cli": "ChatGPT CLI",
    "perplexity": "Perplexity",
    "gemini_cli": "Gemini CLI",
}


class ReportGenerator:
    """Produce markdown tables and SVG charts from agent scorecards."""

    def __init__(self, scorecards: Dict[str, AgentScorecard]):
        self.scorecards = scorecards

    # ── Markdown tables ───────────────────────────────────────────────────

    def overall_comparison_table(self) -> str:
        header = "| Agent | " + " | ".join(DOMAIN_LABELS.get(d, d.title()) for d in DOMAINS) + " | Overall |"
        sep = "|" + "|".join(["---"] * (len(DOMAINS) + 2)) + "|"
        rows = []
        for agent, card in self.scorecards.items():
            label = AGENT_LABELS.get(agent, agent)
            cells = []
            for d in DOMAINS:
                ds = card.domain_scores.get(d)
                cells.append(f"{ds.aggregate:.0f}" if (ds and ds.task_scores) else "—")
            cells.append(f"**{card.overall_score:.0f}**")
            rows.append(f"| {label} | " + " | ".join(cells) + " |")
        return "\n".join([header, sep] + rows)

    def metrics_summary_table(self) -> str:
        header = "| Agent | Domains | Tasks | Avg Latency (s) | Avg Tokens/Task | Resume | Model Switch |"
        sep = "|---|---|---|---|---|---|---|"
        rows = []
        for agent, card in self.scorecards.items():
            m = card.metrics_summary
            label = AGENT_LABELS.get(agent, agent)
            n_domains = sum(1 for d in DOMAINS if card.domain_scores.get(d) and card.domain_scores[d].task_scores)
            n_tasks = m.get("tasks_completed", 0)
            rows.append(
                f"| {label} "
                f"| {n_domains} "
                f"| {n_tasks} "
                f"| {m.get('avg_latency_s', '—')} "
                f"| {m.get('avg_tokens', '—'):,} "
                f"| {m.get('resume_rate', 0):.0%} "
                f"| {m.get('model_switch_rate', 0):.0%} |"
            )
        return "\n".join([header, sep] + rows)

    def feature_comparison_table(self) -> str:
        # Order: GeekCode first, then alphabetical
        agents = ["geekcode"] + [a for a in ALL_AGENTS if a != "geekcode"]
        # Feature flags per agent
        feature_map = {
            "Filesystem State":    {"geekcode": True},
            "Resume After Close":  {"geekcode": True},
            "Token Caching":       {"geekcode": True},
            "Model Switching":     {"geekcode": True},
            "Multi-Domain":        {"geekcode": True, "chatgpt_cli": True, "gemini_cli": True, "perplexity": True},
            "Open Source":         {"geekcode": True, "aider": True, "codex_cli": True},
            "Local Models (Ollama)": {"geekcode": True, "aider": True},
            "Edit-Test Loop":      {"geekcode": True, "claude_code": True, "codex_cli": True, "aider": True},
            "MCPorter (lean MCP)": {"geekcode": True},
        }
        agents_display = [AGENT_LABELS.get(a, a) for a in agents]
        header = "| Feature | " + " | ".join(agents_display) + " |"
        sep = "|---|" + "|".join(["---"] * len(agents)) + "|"
        rows = []
        for name, flags in feature_map.items():
            cells = ["✅" if flags.get(a, False) else "❌" for a in agents]
            rows.append(f"| {name} | " + " | ".join(cells) + " |")
        return "\n".join([header, sep] + rows)

    # ── SVG Charts ────────────────────────────────────────────────────────

    def radar_chart_svg(self, width: int = 660, height: int = 500) -> str:
        """4-axis spider/radar chart comparing agents across domains."""
        cx, cy = width / 2, height / 2
        radius = min(cx, cy) - 80
        n = len(DOMAINS)
        angles = [2 * math.pi * i / n - math.pi / 2 for i in range(n)]

        def polar(angle: float, r: float):
            return cx + r * math.cos(angle), cy + r * math.sin(angle)

        lines: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="font-family:system-ui,sans-serif;background:#fff">',
            f'<text x="{cx}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1a1a2e">Domain Score Comparison</text>',
        ]

        # Grid rings
        for level in (0.25, 0.50, 0.75, 1.0):
            r = radius * level
            pts = " ".join(f"{polar(a, r)[0]:.1f},{polar(a, r)[1]:.1f}" for a in angles)
            lines.append(f'<polygon points="{pts}" fill="none" stroke="#e2e8f0" stroke-width="1"/>')
            lx, ly = polar(angles[0], r)
            lines.append(f'<text x="{lx + 4:.0f}" y="{ly - 4:.0f}" font-size="10" fill="#94a3b8">{int(level*100)}</text>')

        # Axis lines and labels
        for i, domain in enumerate(DOMAINS):
            ex, ey = polar(angles[i], radius)
            lines.append(f'<line x1="{cx}" y1="{cy}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#cbd5e1" stroke-width="1"/>')
            lx, ly = polar(angles[i], radius + 22)
            lines.append(f'<text x="{lx:.0f}" y="{ly:.0f}" text-anchor="middle" font-size="13" font-weight="600" fill="#334155">{DOMAIN_LABELS.get(domain, domain.title())}</text>')

        # Agent polygons (skip agents with no scores in any domain)
        for agent, card in self.scorecards.items():
            colour = AGENT_COLOURS.get(agent, "#888")
            has_any = any(
                (card.domain_scores.get(d) and card.domain_scores[d].task_scores)
                for d in DOMAINS
            )
            if not has_any:
                continue
            pts = []
            for i, domain in enumerate(DOMAINS):
                ds = card.domain_scores.get(domain)
                score = (ds.aggregate / 100.0) if (ds and ds.task_scores) else 0
                x, y = polar(angles[i], radius * score)
                pts.append(f"{x:.1f},{y:.1f}")
            pts_str = " ".join(pts)
            lines.append(f'<polygon points="{pts_str}" fill="{colour}" fill-opacity="0.15" stroke="{colour}" stroke-width="2.5"/>')
            # Dots on vertices
            for pt in pts:
                px, py = pt.split(",")
                lines.append(f'<circle cx="{px}" cy="{py}" r="4" fill="{colour}"/>')

        # Legend — evenly spaced across the full width
        ly = height - 40
        n_agents = len(self.scorecards)
        spacing = (width - 80) / max(n_agents, 1)
        lx_start = 40
        for i, agent in enumerate(self.scorecards):
            colour = AGENT_COLOURS.get(agent, "#888")
            label = AGENT_LABELS.get(agent, agent)
            x = lx_start + i * spacing
            lines.append(f'<rect x="{x:.0f}" y="{ly}" width="14" height="14" rx="3" fill="{colour}"/>')
            lines.append(f'<text x="{x + 20:.0f}" y="{ly + 12}" font-size="12" fill="#475569">{label}</text>')

        lines.append("</svg>")
        return "\n".join(lines)

    def bar_chart_svg(self, width: int = 600, height: int = 340) -> str:
        """Grouped bar chart — overall scores per agent."""
        agents = list(self.scorecards.keys())
        if not agents:
            return ""

        margin_l, margin_r, margin_t, margin_b = 60, 30, 50, 60
        chart_w = width - margin_l - margin_r
        chart_h = height - margin_t - margin_b
        bar_w = chart_w / max(len(agents), 1) * 0.6
        gap = chart_w / max(len(agents), 1)

        lines: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="font-family:system-ui,sans-serif;background:#fff">',
            f'<text x="{width/2}" y="28" text-anchor="middle" font-size="16" font-weight="bold" fill="#1a1a2e">Overall Benchmark Scores</text>',
        ]

        # Y axis grid
        for tick in range(0, 101, 20):
            y = margin_t + chart_h - (tick / 100) * chart_h
            lines.append(f'<line x1="{margin_l}" y1="{y:.0f}" x2="{width - margin_r}" y2="{y:.0f}" stroke="#e2e8f0" stroke-width="1"/>')
            lines.append(f'<text x="{margin_l - 8}" y="{y + 4:.0f}" text-anchor="end" font-size="11" fill="#94a3b8">{tick}</text>')

        # Bars
        for i, agent in enumerate(agents):
            card = self.scorecards[agent]
            score = card.overall_score
            colour = AGENT_COLOURS.get(agent, "#888")
            label = AGENT_LABELS.get(agent, agent)

            x = margin_l + i * gap + (gap - bar_w) / 2
            bar_h = (score / 100) * chart_h
            y = margin_t + chart_h - bar_h

            lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{colour}"/>')
            # Score label above bar
            lines.append(f'<text x="{x + bar_w/2:.1f}" y="{y - 6:.0f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{colour}">{score:.0f}</text>')
            # Agent name below bar
            lines.append(f'<text x="{x + bar_w/2:.1f}" y="{margin_t + chart_h + 20:.0f}" text-anchor="middle" font-size="12" fill="#475569">{label}</text>')

        lines.append("</svg>")
        return "\n".join(lines)

    def metrics_bar_chart_svg(self, metric: str = "avg_latency_s", label: str = "Avg Latency (s)", width: int = 600, height: int = 300) -> str:
        """Single-metric horizontal bar chart."""
        agents = list(self.scorecards.keys())
        if not agents:
            return ""

        values = [self.scorecards[a].metrics_summary.get(metric, 0) for a in agents]
        max_val = max(values) if values else 1
        if max_val == 0:
            max_val = 1

        margin_l, margin_r, margin_t, margin_b = 120, 40, 50, 30
        chart_w = width - margin_l - margin_r
        chart_h = height - margin_t - margin_b
        bar_h = chart_h / max(len(agents), 1) * 0.65
        gap = chart_h / max(len(agents), 1)

        lines: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="font-family:system-ui,sans-serif;background:#fff">',
            f'<text x="{width/2}" y="28" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a1a2e">{label}</text>',
        ]

        for i, agent in enumerate(agents):
            colour = AGENT_COLOURS.get(agent, "#888")
            display = AGENT_LABELS.get(agent, agent)
            val = values[i]
            y = margin_t + i * gap + (gap - bar_h) / 2
            w = (val / max_val) * chart_w

            lines.append(f'<text x="{margin_l - 8}" y="{y + bar_h/2 + 4:.0f}" text-anchor="end" font-size="12" fill="#475569">{display}</text>')
            lines.append(f'<rect x="{margin_l}" y="{y:.1f}" width="{w:.1f}" height="{bar_h:.1f}" rx="4" fill="{colour}"/>')
            lines.append(f'<text x="{margin_l + w + 6:.0f}" y="{y + bar_h/2 + 4:.0f}" font-size="12" font-weight="bold" fill="{colour}">{val:,.1f}</text>')

        lines.append("</svg>")
        return "\n".join(lines)

    def domain_bar_chart_svg(self, domain: str, width: int = 500, height: int = 300) -> str:
        """Bar chart for a single domain — only includes agents that compete in it."""
        agents_in_domain = []
        for agent, card in self.scorecards.items():
            ds = card.domain_scores.get(domain)
            if ds and ds.task_scores:
                agents_in_domain.append((agent, ds.aggregate))
        if not agents_in_domain:
            return ""

        margin_l, margin_r, margin_t, margin_b = 60, 30, 50, 60
        chart_w = width - margin_l - margin_r
        chart_h = height - margin_t - margin_b
        n = len(agents_in_domain)
        bar_w = chart_w / max(n, 1) * 0.6
        gap = chart_w / max(n, 1)

        lines: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="font-family:system-ui,sans-serif;background:#fff">',
            f'<text x="{width/2}" y="28" text-anchor="middle" font-size="15" font-weight="bold" fill="#1a1a2e">{DOMAIN_LABELS.get(domain, domain.title())} — Score Comparison</text>',
        ]

        for tick in range(0, 101, 20):
            y = margin_t + chart_h - (tick / 100) * chart_h
            lines.append(f'<line x1="{margin_l}" y1="{y:.0f}" x2="{width - margin_r}" y2="{y:.0f}" stroke="#e2e8f0" stroke-width="1"/>')
            lines.append(f'<text x="{margin_l - 8}" y="{y + 4:.0f}" text-anchor="end" font-size="11" fill="#94a3b8">{tick}</text>')

        for i, (agent, score) in enumerate(agents_in_domain):
            colour = AGENT_COLOURS.get(agent, "#888")
            label = AGENT_LABELS.get(agent, agent)
            x = margin_l + i * gap + (gap - bar_w) / 2
            bar_h = (score / 100) * chart_h
            y = margin_t + chart_h - bar_h
            lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{colour}"/>')
            lines.append(f'<text x="{x + bar_w/2:.1f}" y="{y - 6:.0f}" text-anchor="middle" font-size="13" font-weight="bold" fill="{colour}">{score:.0f}</text>')
            lines.append(f'<text x="{x + bar_w/2:.1f}" y="{margin_t + chart_h + 20:.0f}" text-anchor="middle" font-size="12" fill="#475569">{label}</text>')

        lines.append("</svg>")
        return "\n".join(lines)

    def domain_latency_chart_svg(self, domain: str, width: int = 500, height: int = 260) -> str:
        """Horizontal bar chart of avg latency for agents in a single domain."""
        agents_in = []
        for agent, card in self.scorecards.items():
            ds = card.domain_scores.get(domain)
            if not (ds and ds.task_scores):
                continue
            # Compute per-domain latency from results
            from benchmarks.models import RESULTS_DIR, BenchmarkResult
            domain_dir = RESULTS_DIR / agent / domain
            lats = []
            if domain_dir.exists():
                for p in sorted(domain_dir.glob("*.yaml")):
                    try:
                        r = BenchmarkResult.load(p)
                        lats.append(r.metrics.latency_seconds)
                    except Exception:
                        continue
            avg_lat = sum(lats) / max(len(lats), 1) if lats else 0
            agents_in.append((agent, avg_lat))
        if not agents_in:
            return ""

        max_val = max(v for _, v in agents_in) if agents_in else 1
        if max_val == 0:
            max_val = 1

        margin_l, margin_r, margin_t, margin_b = 120, 50, 45, 20
        chart_w = width - margin_l - margin_r
        chart_h = height - margin_t - margin_b
        n = len(agents_in)
        bar_h = chart_h / max(n, 1) * 0.65
        gap_h = chart_h / max(n, 1)

        lines: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="font-family:system-ui,sans-serif;background:#fff">',
            f'<text x="{width/2}" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">{DOMAIN_LABELS.get(domain, domain.title())} — Avg Latency (s)</text>',
        ]
        for i, (agent, val) in enumerate(agents_in):
            colour = AGENT_COLOURS.get(agent, "#888")
            display = AGENT_LABELS.get(agent, agent)
            y = margin_t + i * gap_h + (gap_h - bar_h) / 2
            w = (val / max_val) * chart_w
            lines.append(f'<text x="{margin_l - 8}" y="{y + bar_h/2 + 4:.0f}" text-anchor="end" font-size="12" fill="#475569">{display}</text>')
            lines.append(f'<rect x="{margin_l}" y="{y:.1f}" width="{w:.1f}" height="{bar_h:.1f}" rx="4" fill="{colour}"/>')
            lines.append(f'<text x="{margin_l + w + 6:.0f}" y="{y + bar_h/2 + 4:.0f}" font-size="12" font-weight="bold" fill="{colour}">{val:.1f}s</text>')
        lines.append("</svg>")
        return "\n".join(lines)

    def domain_tokens_chart_svg(self, domain: str, width: int = 500, height: int = 260) -> str:
        """Horizontal bar chart of avg tokens/task for agents in a single domain."""
        agents_in = []
        for agent, card in self.scorecards.items():
            ds = card.domain_scores.get(domain)
            if not (ds and ds.task_scores):
                continue
            from benchmarks.models import RESULTS_DIR, BenchmarkResult
            domain_dir = RESULTS_DIR / agent / domain
            toks = []
            if domain_dir.exists():
                for p in sorted(domain_dir.glob("*.yaml")):
                    try:
                        r = BenchmarkResult.load(p)
                        toks.append(r.metrics.tokens_used)
                    except Exception:
                        continue
            avg_tok = sum(toks) / max(len(toks), 1) if toks else 0
            agents_in.append((agent, avg_tok))
        if not agents_in:
            return ""

        max_val = max(v for _, v in agents_in) if agents_in else 1
        if max_val == 0:
            max_val = 1

        margin_l, margin_r, margin_t, margin_b = 120, 60, 45, 20
        chart_w = width - margin_l - margin_r
        chart_h = height - margin_t - margin_b
        n = len(agents_in)
        bar_h = chart_h / max(n, 1) * 0.65
        gap_h = chart_h / max(n, 1)

        lines: List[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'width="{width}" height="{height}" style="font-family:system-ui,sans-serif;background:#fff">',
            f'<text x="{width/2}" y="24" text-anchor="middle" font-size="14" font-weight="bold" fill="#1a1a2e">{DOMAIN_LABELS.get(domain, domain.title())} — Avg Tokens/Task</text>',
        ]
        for i, (agent, val) in enumerate(agents_in):
            colour = AGENT_COLOURS.get(agent, "#888")
            display = AGENT_LABELS.get(agent, agent)
            y = margin_t + i * gap_h + (gap_h - bar_h) / 2
            w = (val / max_val) * chart_w
            lines.append(f'<text x="{margin_l - 8}" y="{y + bar_h/2 + 4:.0f}" text-anchor="end" font-size="12" fill="#475569">{display}</text>')
            lines.append(f'<rect x="{margin_l}" y="{y:.1f}" width="{w:.1f}" height="{bar_h:.1f}" rx="4" fill="{colour}"/>')
            lines.append(f'<text x="{margin_l + w + 6:.0f}" y="{y + bar_h/2 + 4:.0f}" font-size="12" font-weight="bold" fill="{colour}">{val:,.0f}</text>')
        lines.append("</svg>")
        return "\n".join(lines)

    # ── File output ───────────────────────────────────────────────────────

    def save_svgs(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "radar_chart.svg").write_text(self.radar_chart_svg())
        # Domain-specific charts — fair comparison (only agents that compete)
        for domain in DOMAINS:
            (out_dir / f"{domain}_scores.svg").write_text(self.domain_bar_chart_svg(domain))
            (out_dir / f"{domain}_latency.svg").write_text(self.domain_latency_chart_svg(domain))
            (out_dir / f"{domain}_tokens.svg").write_text(self.domain_tokens_chart_svg(domain))

    def save_report(self, path: Path) -> None:
        """Write a full markdown report."""
        path.parent.mkdir(parents=True, exist_ok=True)
        sections = [
            "# GeekCode Benchmark Report\n",
            f"_Auto-generated comparison of {len(self.scorecards)} agents across {len(DOMAINS)} domains._\n",
            "## Overall Scores\n",
            self.overall_comparison_table(),
            "\n## Domain Comparison (Radar)\n",
            "![Radar Chart](radar_chart.svg)\n",
            "## Metrics Summary\n",
            self.metrics_summary_table(),
            "\n## Feature Comparison\n",
            self.feature_comparison_table(),
            "\n---\n",
            "_Run benchmarks yourself: `geekcode` → `/benchmark run` → `/benchmark report`_\n",
        ]

        # Per-domain breakdowns with charts
        sections.append("\n## Per-Domain Breakdown\n")
        for domain in DOMAINS:
            sections.append(f"\n### {DOMAIN_LABELS.get(domain, domain.title())}\n")
            sections.append(f"![{DOMAIN_LABELS.get(domain, domain.title())} Scores]({domain}_scores.svg)\n")
            task_names = TASK_NAMES.get(domain, [f"Task {i+1}" for i in range(20)])
            n_tasks = len(task_names)
            header = "| Agent | " + " | ".join(task_names) + " | Avg |"
            sep = "|---|" + "|".join(["---"] * (n_tasks + 1)) + "|"
            rows = []
            for agent, card in self.scorecards.items():
                label = AGENT_LABELS.get(agent, agent)
                ds = card.domain_scores.get(domain)
                if not ds or not ds.task_scores:
                    continue
                cells = [f"{ds.task_scores.get(i+1, 0):.0f}" for i in range(n_tasks)]
                cells.append(f"**{ds.aggregate:.0f}**")
                rows.append(f"| {label} | " + " | ".join(cells) + " |")
            sections.extend([header, sep] + rows)
            sections.append(f"\n![{DOMAIN_LABELS.get(domain, domain.title())} Latency]({domain}_latency.svg)")
            sections.append(f"![{DOMAIN_LABELS.get(domain, domain.title())} Tokens]({domain}_tokens.svg)\n")

        path.write_text("\n".join(sections))

    def generate_readme_section(self) -> str:
        """Compact benchmark section suitable for README.md."""
        lines = [
            "## Benchmarks\n",
            "GeekCode is benchmarked against domain-specific competitors across 4 domains.\n",
            "### Overall Scores\n",
            self.overall_comparison_table(),
            "\n### Radar Chart\n",
            '<p align="center">',
            '  <img src="docs/benchmarks/radar_chart.svg" alt="Benchmark Radar Chart" width="500">',
            "</p>\n",
            "### Key Metrics\n",
            self.metrics_summary_table(),
            "\n### Features\n",
            self.feature_comparison_table(),
            "\n<details>",
            "<summary><strong>Run benchmarks yourself</strong></summary>\n",
            "```bash",
            "geekcode",
            "# Inside the REPL:",
            "/benchmark run          # Run all domains",
            "/benchmark run coding   # Run single domain",
            "/benchmark report       # Generate charts & report",
            "```",
            "\nFull report: [`docs/benchmarks/report.md`](docs/benchmarks/report.md)",
            "</details>\n",
        ]
        return "\n".join(lines)


# ── CLI entry-point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    from benchmarks.evaluate import Evaluator

    evaluator = Evaluator()
    scorecards = evaluator.compare_agents()
    gen = ReportGenerator(scorecards)

    out_dir = Path(__file__).resolve().parent.parent / "docs" / "benchmarks"
    gen.save_svgs(out_dir)
    gen.save_report(out_dir / "report.md")
    print(f"Report and SVGs saved to {out_dir}")
