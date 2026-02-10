"""Evaluator — scores benchmark results against expected.md rubrics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from benchmarks.models import (
    ALL_AGENTS,
    BENCHMARKS_DIR,
    DOMAINS,
    RESULTS_DIR,
    RUBRIC_WEIGHTS,
    AgentScorecard,
    BenchmarkResult,
    DomainScore,
)


class Evaluator:
    """Scores agent outputs by matching against expected.md checklist items."""

    def __init__(self, manual_scores: Optional[Dict[str, Dict]] = None):
        """
        Parameters
        ----------
        manual_scores : optional override dict keyed ``"{agent}/{domain}/task{id}"``
            with values ``{"accuracy": 0.85, ...}`` for precise manual evaluation.
        """
        self.manual_scores = manual_scores or {}

    # ── Single task ───────────────────────────────────────────────────────

    def evaluate_task(self, result: BenchmarkResult) -> float:
        """Score a single task result (0-100)."""
        key = f"{result.agent}/{result.domain}/task{result.task_id}"

        # Manual override takes priority
        if key in self.manual_scores:
            return float(self.manual_scores[key].get("score", 0))

        if not result.completed:
            return 0.0

        # Pre-scored accuracy (set by runner or seed) takes priority
        if result.metrics.accuracy > 0:
            return round(result.metrics.accuracy * 100, 1)

        # Load expected.md checklist for the domain
        checklist = self._load_checklist(result.domain, result.task_id)

        # Heuristic scoring against checklist
        heuristic_score = 0.0
        if checklist and result.output:
            hits = 0
            partials = 0
            for item in checklist:
                s = self._score_checklist_item(item, result.output)
                if s >= 0.9:
                    hits += 1
                elif s >= 0.4:
                    partials += 1
            total = len(checklist)
            if total > 0:
                heuristic_score = ((hits * 1.0) + (partials * 0.5)) / total * 100

        if heuristic_score >= 10:
            return round(heuristic_score, 1)

        # Completed but no data to score
        return 50.0 if result.output else 0.0

    # ── Domain level ──────────────────────────────────────────────────────

    def evaluate_domain(self, agent: str, domain: str) -> DomainScore:
        """Load all results for *agent/domain* and produce a DomainScore."""
        results_dir = RESULTS_DIR / agent / domain
        results = self._load_results(results_dir)

        task_scores: Dict[int, float] = {}
        for r in results:
            task_scores[r.task_id] = self.evaluate_task(r)

        aggregate = sum(task_scores.values()) / max(len(task_scores), 1)

        # Build rubric breakdown
        weights = RUBRIC_WEIGHTS.get(domain, {})
        rubric_scores = {k: aggregate / 100.0 for k in weights}

        return DomainScore(
            domain=domain,
            task_scores=task_scores,
            rubric_scores=rubric_scores,
            aggregate=round(aggregate, 1),
        )

    # ── Agent level ───────────────────────────────────────────────────────

    def evaluate_agent(self, agent: str) -> AgentScorecard:
        domain_scores: Dict[str, DomainScore] = {}
        for d in DOMAINS:
            domain_scores[d] = self.evaluate_domain(agent, d)

        scores = [ds.aggregate for ds in domain_scores.values() if ds.task_scores]
        overall = sum(scores) / max(len(scores), 1)

        # Aggregate metrics from results
        metrics_summary = self._aggregate_metrics(agent)

        return AgentScorecard(
            agent_name=agent,
            domain_scores=domain_scores,
            overall_score=round(overall, 1),
            metrics_summary=metrics_summary,
        )

    # ── Compare all agents ────────────────────────────────────────────────

    def compare_agents(self, agents: Optional[List[str]] = None) -> Dict[str, AgentScorecard]:
        agents = agents or ALL_AGENTS
        return {a: self.evaluate_agent(a) for a in agents}

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    def _load_checklist(domain: str, task_id: int) -> List[str]:
        """Parse ``- [ ]`` items from the relevant task section in expected.md."""
        expected_path = BENCHMARKS_DIR / domain / "expected.md"
        if not expected_path.exists():
            return []

        text = expected_path.read_text()

        # Find the section for this task
        pattern = rf"## Task {task_id}:.*?(?=\n## Task \d+:|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            return []

        section = match.group(0)
        items = re.findall(r"-\s*\[ ?\]\s*(.+)", section)
        return items

    @staticmethod
    def _score_checklist_item(item: str, output: str) -> float:
        """Heuristic match of a checklist description against agent output.

        Returns 1.0 (strong match), 0.5 (partial), or 0.0 (no match).
        """
        output_lower = output.lower()

        # Extract meaningful keywords from checklist item (3+ char words)
        keywords = [w.lower() for w in re.findall(r"[a-zA-Z]{3,}", item)]
        if not keywords:
            return 0.5

        matched = sum(1 for kw in keywords if kw in output_lower)
        ratio = matched / len(keywords)

        if ratio >= 0.6:
            return 1.0
        if ratio >= 0.3:
            return 0.5
        return 0.0

    @staticmethod
    def _load_results(results_dir: Path) -> List[BenchmarkResult]:
        if not results_dir.exists():
            return []
        results = []
        for p in sorted(results_dir.glob("*.yaml")):
            try:
                results.append(BenchmarkResult.load(p))
            except Exception:
                continue
        return results

    def _aggregate_metrics(self, agent: str) -> Dict[str, Any]:
        """Summarise latency, tokens, resume rate, etc."""
        agent_dir = RESULTS_DIR / agent
        if not agent_dir.exists():
            return {}

        latencies: List[float] = []
        tokens: List[int] = []
        resumes = 0
        model_switches = 0
        total = 0

        for p in agent_dir.rglob("*.yaml"):
            try:
                r = BenchmarkResult.load(p)
            except Exception:
                continue
            total += 1
            latencies.append(r.metrics.latency_seconds)
            tokens.append(r.metrics.tokens_used)
            if r.metrics.resume_success:
                resumes += 1
            if r.metrics.model_switch_success:
                model_switches += 1

        return {
            "avg_latency_s": round(sum(latencies) / max(len(latencies), 1), 2),
            "total_tokens": sum(tokens),
            "avg_tokens": round(sum(tokens) / max(len(tokens), 1)),
            "resume_rate": round(resumes / max(total, 1), 2),
            "model_switch_rate": round(model_switches / max(total, 1), 2),
            "tasks_completed": total,
        }


# ── CLI entry-point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse, json

    parser = argparse.ArgumentParser(description="GeekCode Benchmark Evaluator")
    parser.add_argument("--agent", help="Evaluate a single agent")
    args = parser.parse_args()

    evaluator = Evaluator()
    if args.agent:
        card = evaluator.evaluate_agent(args.agent)
        print(yaml.dump(card.to_dict(), default_flow_style=False))
    else:
        cards = evaluator.compare_agents()
        for name, card in cards.items():
            print(f"\n{'='*50}")
            print(yaml.dump(card.to_dict(), default_flow_style=False))
