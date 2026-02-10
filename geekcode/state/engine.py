"""
GeekCode State Engine - Persistent state management for resumable workflows.

This module provides the StateEngine class for saving and loading task state,
enabling crash recovery and resumable workflows.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TaskState:
    """
    Represents the state of a task execution.

    This dataclass holds all information needed to resume a task
    after interruption.
    """

    task_id: str
    task_description: str
    status: str  # pending, running, completed, error, paused
    current_step: int
    created_at: datetime
    updated_at: datetime
    model: Optional[str] = None
    resume_mode: bool = False
    step_phase: str = "init"
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    token_usage: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "task_description": self.task_description,
            "status": self.status,
            "current_step": self.current_step,
            "step_phase": self.step_phase,
            "model": self.model,
            "resume_mode": self.resume_mode,
            "completed_steps": self.completed_steps,
            "pending_steps": self.pending_steps,
            "context": self.context,
            "error": self.error,
            "token_usage": self.token_usage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskState":
        """Create a TaskState from a dictionary."""
        return cls(
            task_id=data["task_id"],
            task_description=data["task_description"],
            status=data["status"],
            current_step=data["current_step"],
            step_phase=data.get("step_phase", "init"),
            model=data.get("model"),
            resume_mode=data.get("resume_mode", False),
            completed_steps=data.get("completed_steps", []),
            pending_steps=data.get("pending_steps", []),
            context=data.get("context", {}),
            error=data.get("error"),
            token_usage=data.get("token_usage", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class StateEngine:
    """
    Engine for managing persistent task state.

    The StateEngine handles:
    - Saving task state to YAML files
    - Loading task state for resumption
    - Listing resumable tasks
    - Cleaning up old state files

    State files are stored in:
    - Local: .geekcode/state/

    Example:
        >>> engine = StateEngine()
        >>> state = TaskState(task_id="123", ...)
        >>> engine.save(state)
        >>> loaded = engine.load("123")
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize the StateEngine.

        Args:
            state_dir: Directory for state files. If None, uses default locations.
        """
        if state_dir:
            self.state_dir = Path(state_dir)
        else:
            # Use project-local .geekcode/state/ only
            self.state_dir = Path.cwd() / ".geekcode" / "state"

        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: TaskState) -> Path:
        """
        Save task state to a YAML file.

        Args:
            state: The TaskState to save.

        Returns:
            Path to the saved state file.
        """
        state_file = self.state_dir / f"{state.task_id}.yaml"

        with open(state_file, "w") as f:
            yaml.dump(state.to_dict(), f, default_flow_style=False, sort_keys=False)

        return state_file

    def load(self, task_id: str) -> Optional[TaskState]:
        """
        Load task state from file.

        Args:
            task_id: The task ID to load.

        Returns:
            TaskState if found, None otherwise.
        """
        state_file = self.state_dir / f"{task_id}.yaml"

        if not state_file.exists():
            return None

        with open(state_file) as f:
            data = yaml.safe_load(f)

        return TaskState.from_dict(data)

    def load_latest(self) -> Optional[TaskState]:
        """
        Load the most recently updated task state.

        Returns:
            The most recent TaskState, or None if no states exist.
        """
        state_files = list(self.state_dir.glob("*.yaml"))

        if not state_files:
            return None

        # Sort by modification time, most recent first
        state_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        # Find the first non-completed state, or return the latest
        for state_file in state_files:
            try:
                with open(state_file) as f:
                    data = yaml.safe_load(f)
                state = TaskState.from_dict(data)

                if state.status not in ("completed", "error"):
                    return state
            except Exception:
                continue

        # If all are completed/errored, return the most recent
        try:
            with open(state_files[0]) as f:
                data = yaml.safe_load(f)
            return TaskState.from_dict(data)
        except Exception:
            return None

    def list_resumable(self) -> List[TaskState]:
        """
        List all resumable (non-completed) task states.

        Returns:
            List of TaskState objects that can be resumed.
        """
        resumable = []

        for state_file in self.state_dir.glob("*.yaml"):
            try:
                with open(state_file) as f:
                    data = yaml.safe_load(f)
                state = TaskState.from_dict(data)

                if state.status in ("running", "pending", "paused"):
                    resumable.append(state)
            except Exception:
                continue

        # Sort by updated_at, most recent first
        resumable.sort(key=lambda s: s.updated_at, reverse=True)
        return resumable

    def delete(self, task_id: str) -> bool:
        """
        Delete a task state file.

        Args:
            task_id: The task ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        state_file = self.state_dir / f"{task_id}.yaml"

        if state_file.exists():
            state_file.unlink()
            return True
        return False

    def cleanup(self, max_age_days: int = 30, max_count: int = 100) -> int:
        """
        Clean up old state files.

        Args:
            max_age_days: Delete states older than this.
            max_count: Keep at most this many states.

        Returns:
            Number of files deleted.
        """
        state_files = list(self.state_dir.glob("*.yaml"))
        deleted = 0

        # Delete by age
        now = datetime.utcnow()
        for state_file in state_files:
            try:
                with open(state_file) as f:
                    data = yaml.safe_load(f)
                updated_at = datetime.fromisoformat(data["updated_at"])
                age = (now - updated_at).days

                if age > max_age_days:
                    state_file.unlink()
                    deleted += 1
            except Exception:
                continue

        # Delete by count
        remaining = list(self.state_dir.glob("*.yaml"))
        if len(remaining) > max_count:
            remaining.sort(key=lambda p: p.stat().st_mtime)
            for state_file in remaining[:-max_count]:
                try:
                    state_file.unlink()
                    deleted += 1
                except Exception:
                    continue

        return deleted

    def create_checkpoint(self, state: TaskState, checkpoint_name: str) -> Path:
        """
        Create a named checkpoint of the current state.

        Args:
            state: The TaskState to checkpoint.
            checkpoint_name: Name for the checkpoint.

        Returns:
            Path to the checkpoint file.
        """
        checkpoint_dir = self.state_dir / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)

        checkpoint_file = checkpoint_dir / f"{state.task_id}_{checkpoint_name}.yaml"

        with open(checkpoint_file, "w") as f:
            yaml.dump(state.to_dict(), f, default_flow_style=False, sort_keys=False)

        return checkpoint_file

    def load_checkpoint(self, task_id: str, checkpoint_name: str) -> Optional[TaskState]:
        """
        Load a specific checkpoint.

        Args:
            task_id: The task ID.
            checkpoint_name: Name of the checkpoint.

        Returns:
            TaskState if found, None otherwise.
        """
        checkpoint_file = self.state_dir / "checkpoints" / f"{task_id}_{checkpoint_name}.yaml"

        if not checkpoint_file.exists():
            return None

        with open(checkpoint_file) as f:
            data = yaml.safe_load(f)

        return TaskState.from_dict(data)

    def list_checkpoints(self, task_id: str) -> List[str]:
        """
        List available checkpoints for a task.

        Args:
            task_id: The task ID.

        Returns:
            List of checkpoint names.
        """
        checkpoint_dir = self.state_dir / "checkpoints"
        if not checkpoint_dir.exists():
            return []

        checkpoints = []
        prefix = f"{task_id}_"

        for checkpoint_file in checkpoint_dir.glob(f"{prefix}*.yaml"):
            name = checkpoint_file.stem[len(prefix) :]
            checkpoints.append(name)

        return checkpoints
