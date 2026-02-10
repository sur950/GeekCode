"""Benchmark runner — executes tasks against GeekCode, saves results as YAML."""

from __future__ import annotations

import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from benchmarks.models import (
    BENCHMARKS_DIR,
    DOMAINS,
    RESULTS_DIR,
    BenchmarkResult,
    TaskInput,
    TaskMetrics,
)


class BenchmarkRunner:
    """Discovers and runs benchmark tasks, persisting results to disk."""

    def __init__(self, agent_name: str = "geekcode"):
        self.agent_name = agent_name

    # ── Discovery ─────────────────────────────────────────────────────────

    def discover_tasks(self, domain: Optional[str] = None) -> List[TaskInput]:
        """Parse ``## Task N`` headings from task.md files."""
        domains = [domain] if domain else DOMAINS
        tasks: List[TaskInput] = []
        for d in domains:
            task_md = BENCHMARKS_DIR / d / "task.md"
            if not task_md.exists():
                continue
            text = task_md.read_text()
            tasks.extend(TaskInput.parse_task_md(d, text))
        return tasks

    # ── Single task execution ─────────────────────────────────────────────

    def run_task(
        self,
        task: TaskInput,
        scenario: str = "baseline",
        model: Optional[str] = None,
    ) -> BenchmarkResult:
        """Run one task inside a temporary workspace and measure it."""
        workspace = Path(tempfile.mkdtemp(prefix="geekcode_bench_"))
        try:
            # Copy data files into workspace
            data_src = BENCHMARKS_DIR / task.domain / "data"
            data_dst = workspace / "data"
            if data_src.exists():
                shutil.copytree(data_src, data_dst)

            # Write a minimal .geekcode config so Agent can initialize
            gc_dir = workspace / ".geekcode"
            gc_dir.mkdir()
            config: Dict = {"project": {"name": f"bench-{task.domain}"}}
            if model:
                config["model"] = model
            with open(gc_dir / "config.yaml", "w") as f:
                yaml.dump(config, f)
            with open(gc_dir / "state.yaml", "w") as f:
                yaml.dump({"status": "idle"}, f)

            # Build the prompt from the task description
            prompt = (
                f"You are being benchmarked on a {task.domain} task.\n\n"
                f"{task.description}\n\n"
                "Provide a complete, high-quality answer."
            )
            input_files = [str(data_dst / Path(p).name) for p in task.input_files if (data_dst / Path(p).name).exists()] if data_dst.exists() else []

            # Execute via Agent
            from geekcode.core.agent import Agent

            agent = Agent(workspace)
            t0 = time.perf_counter()
            result = agent.run(prompt, files=input_files or None)
            elapsed = time.perf_counter() - t0

            metrics = TaskMetrics(
                latency_seconds=elapsed,
                tokens_used=result.tokens_used,
                tokens_saved=result.tokens_saved,
                cached=result.cached,
            )

            br = BenchmarkResult(
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent=self.agent_name,
                domain=task.domain,
                task_id=task.task_id,
                scenario=scenario,
                model=result.model,
                output=result.output,
                metrics=metrics,
                completed=result.completed,
                error=result.error,
            )
        except Exception as exc:
            br = BenchmarkResult(
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent=self.agent_name,
                domain=task.domain,
                task_id=task.task_id,
                scenario=scenario,
                completed=False,
                error=str(exc),
            )
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

        br.save()
        return br

    # ── Batch execution ───────────────────────────────────────────────────

    def run_domain(self, domain: str, **kwargs) -> List[BenchmarkResult]:
        results = []
        for task in self.discover_tasks(domain):
            results.append(self.run_task(task, **kwargs))
        return results

    def run_all(self, **kwargs) -> List[BenchmarkResult]:
        results = []
        for domain in DOMAINS:
            results.extend(self.run_domain(domain, **kwargs))
        return results

    # ── External result import ────────────────────────────────────────────

    @staticmethod
    def import_external_results(agent: str, file: Path) -> List[BenchmarkResult]:
        """Import manually-entered results for Claude Code / Gemini / Codex.

        The file should be a YAML list of dicts matching BenchmarkResult fields.
        """
        with open(file) as f:
            data = yaml.safe_load(f) or []
        results = []
        for entry in data:
            entry.setdefault("agent", agent)
            br = BenchmarkResult.from_dict(entry)
            br.save()
            results.append(br)
        return results


# ── CLI entry-point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GeekCode Benchmark Runner")
    parser.add_argument("--domain", choices=DOMAINS, help="Run a single domain")
    parser.add_argument("--agent", default="geekcode")
    args = parser.parse_args()

    runner = BenchmarkRunner(agent_name=args.agent)
    if args.domain:
        results = runner.run_domain(args.domain)
    else:
        results = runner.run_all()

    for r in results:
        status = "OK" if r.completed else f"FAIL ({r.error})"
        print(f"  {r.domain}/task{r.task_id} [{r.scenario}] — {status}")
    print(f"\nResults saved to {RESULTS_DIR}")
