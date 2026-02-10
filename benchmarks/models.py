"""Shared data structures for the benchmark pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

DOMAINS = ["coding", "finance", "healthcare", "general"]

DOMAIN_LABELS: Dict[str, str] = {
    "coding": "Coding",
    "finance": "Finance",
    "healthcare": "Healthcare",
    "general": "General/Research",
}

# Domain-specific agent rosters — each domain compared against its best competitors
DOMAIN_AGENTS: Dict[str, List[str]] = {
    "coding":     ["geekcode", "claude_code", "codex_cli", "aider"],
    "finance":    ["geekcode", "perplexity", "chatgpt_cli", "gemini_cli"],
    "healthcare": ["geekcode", "perplexity", "chatgpt_cli", "gemini_cli"],
    "general":    ["geekcode", "perplexity", "chatgpt_cli", "gemini_cli"],
}

# Flat set of all agents (for report generation)
ALL_AGENTS: List[str] = sorted({a for agents in DOMAIN_AGENTS.values() for a in agents})

# Legacy alias for backward compat
AGENTS = ALL_AGENTS

BENCHMARKS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BENCHMARKS_DIR / "results"

# 20 named tasks per domain
TASK_NAMES: Dict[str, List[str]] = {
    "coding": [
        "Parse JSON Config",
        "Add Unit Tests",
        "Refactor Async/Await",
        "Fix Race Condition",
        "REST API Endpoint",
        "Database Migration",
        "Error Handling",
        "Code Review Analysis",
        "SQL Query Optimization",
        "CI Pipeline Setup",
        "Memory Leak Debug",
        "Auth Middleware",
        "API Documentation",
        "Response Caching",
        "Microservice Extract",
        "Structured Logging",
        "CSS Layout Fix",
        "WebSocket Handler",
        "Input Validation",
        "Performance Profile",
    ],
    "finance": [
        "Policy Coverage",
        "Premium Calculation",
        "Risk Assessment",
        "Claims Adjudication",
        "Regulatory Compliance",
        "Financial Statements",
        "Portfolio Risk",
        "Tax Implications",
        "Exclusion Detection",
        "Actuarial Tables",
        "Fraud Patterns",
        "Credit Scoring",
        "Market Trends",
        "Compliance Audit",
        "Investment Review",
        "Liability Assessment",
        "Reinsurance Analysis",
        "Loss Ratio Calc",
        "Underwriting Rules",
        "Financial Forecast",
    ],
    "healthcare": [
        "Clinical Guidelines",
        "Drug Interactions",
        "ICD-10 Coding",
        "Prior Authorization",
        "Medical Necessity",
        "Treatment Protocol",
        "Patient Eligibility",
        "Claims Rules",
        "Formulary Check",
        "Adverse Events",
        "Care Pathways",
        "Quality Metrics",
        "HIPAA Compliance",
        "Utilization Review",
        "Discharge Planning",
        "Population Health",
        "Trial Matching",
        "Record Summary",
        "Benefit Plans",
        "Provider Credentials",
    ],
    "general": [
        "Literature Review",
        "Data Synthesis",
        "Trend Analysis",
        "Comparative Study",
        "Executive Summary",
        "Multi-Source Research",
        "Policy Brief",
        "Technical Report",
        "Gap Analysis",
        "Stakeholder Analysis",
        "SWOT Analysis",
        "Competitive Intel",
        "Regulatory Landscape",
        "Impact Assessment",
        "Best Practices",
        "Case Study",
        "Cross-Domain Synthesis",
        "Scenario Planning",
        "Evidence Mapping",
        "Strategic Recommendation",
    ],
}

# Domain rubric weights  (criterion -> weight)
RUBRIC_WEIGHTS: Dict[str, Dict[str, float]] = {
    "coding": {
        "correctness": 0.40,
        "code_quality": 0.25,
        "best_practices": 0.20,
        "documentation": 0.15,
    },
    "finance": {
        "accuracy": 0.40,
        "citations": 0.25,
        "completeness": 0.20,
        "clarity": 0.15,
    },
    "healthcare": {
        "accuracy": 0.40,
        "completeness": 0.25,
        "citations": 0.20,
        "clarity": 0.15,
    },
    "general": {
        "completeness": 0.30,
        "accuracy": 0.30,
        "coherence": 0.20,
        "depth": 0.20,
    },
}

# ── Dataclasses ──────────────────────────────────────────────────────────────


@dataclass
class TaskInput:
    """Parsed task definition from a domain task.md file."""

    domain: str
    task_id: int
    title: str
    description: str
    input_files: List[str] = field(default_factory=list)
    time_limit_minutes: int = 30

    @staticmethod
    def parse_task_md(domain: str, text: str) -> List["TaskInput"]:
        """Parse ``## Task N`` headings from a task.md file."""
        tasks: List[TaskInput] = []
        # Split on ## Task headings
        parts = re.split(r"(?=^## Task \d+)", text, flags=re.MULTILINE)
        for part in parts:
            m = re.match(r"^## Task (\d+):\s*(.+)", part)
            if not m:
                continue
            task_id = int(m.group(1))
            title = m.group(2).strip()

            # Extract input files listed as `data/...`
            input_files = re.findall(r"`(data/[^`]+)`", part)

            # Extract time limit
            time_match = re.search(r"Task\s+" + str(task_id) + r":\s*(\d+)\s*minutes", part)
            time_limit = int(time_match.group(1)) if time_match else 30

            tasks.append(
                TaskInput(
                    domain=domain,
                    task_id=task_id,
                    title=title,
                    description=part.strip(),
                    input_files=input_files,
                    time_limit_minutes=time_limit,
                )
            )
        return tasks


@dataclass
class TaskMetrics:
    """Raw metrics collected for a single task run."""

    accuracy: float = 0.0
    latency_seconds: float = 0.0
    tokens_used: int = 0
    tokens_saved: int = 0
    cached: bool = False
    resume_success: bool = False
    model_switch_success: bool = False
    context_retention: float = 0.0
    citation_accuracy: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "latency_seconds": round(self.latency_seconds, 2),
            "tokens_used": self.tokens_used,
            "tokens_saved": self.tokens_saved,
            "cached": self.cached,
            "resume_success": self.resume_success,
            "model_switch_success": self.model_switch_success,
            "context_retention": self.context_retention,
            "citation_accuracy": self.citation_accuracy,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskMetrics":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class BenchmarkResult:
    """Result of a single benchmark task execution."""

    timestamp: str = ""
    agent: str = ""
    domain: str = ""
    task_id: int = 0
    scenario: str = "baseline"
    model: str = ""
    output: str = ""
    metrics: TaskMetrics = field(default_factory=TaskMetrics)
    completed: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "agent": self.agent,
            "domain": self.domain,
            "task_id": self.task_id,
            "scenario": self.scenario,
            "model": self.model,
            "output": self.output[:2000],  # truncate for YAML
            "metrics": self.metrics.to_dict(),
            "completed": self.completed,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BenchmarkResult":
        metrics = TaskMetrics.from_dict(d.pop("metrics", {}))
        return cls(metrics=metrics, **{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    def save(self, base_dir: Optional[Path] = None) -> Path:
        """Save result as YAML."""
        base = base_dir or RESULTS_DIR
        out_dir = base / self.agent / self.domain
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{self.scenario}_task{self.task_id}.yaml"
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
        return path

    @classmethod
    def load(cls, path: Path) -> "BenchmarkResult":
        with open(path) as f:
            return cls.from_dict(yaml.safe_load(f))


@dataclass
class DomainScore:
    """Scored result for one agent in one domain."""

    domain: str = ""
    task_scores: Dict[int, float] = field(default_factory=dict)  # task_id -> 0-100
    rubric_scores: Dict[str, float] = field(default_factory=dict)  # criterion -> 0-1
    aggregate: float = 0.0  # weighted 0-100


@dataclass
class AgentScorecard:
    """Complete scorecard for one agent across all domains."""

    agent_name: str = ""
    domain_scores: Dict[str, DomainScore] = field(default_factory=dict)
    overall_score: float = 0.0
    metrics_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "overall_score": round(self.overall_score, 1),
            "domains": {
                d: {
                    "score": round(ds.aggregate, 1),
                    "tasks": ds.task_scores,
                    "rubric": ds.rubric_scores,
                }
                for d, ds in self.domain_scores.items()
            },
            "metrics": self.metrics_summary,
        }
