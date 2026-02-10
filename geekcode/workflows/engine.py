"""
GeekCode Workflow Engine - YAML-driven workflow execution.

This module provides the WorkflowEngine for executing multi-step,
resumable workflows defined in YAML.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from geekcode.state.engine import StateEngine, TaskState


class StepStatus(Enum):
    """Status of a workflow step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""

    name: str
    order: int
    description: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 3
    on_error: str = "stop"  # stop, skip, retry
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Any = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "name": self.name,
            "order": self.order,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "on_error": self.on_error,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStep":
        """Create step from dictionary."""
        step = cls(
            name=data["name"],
            order=data["order"],
            description=data.get("description", ""),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            timeout_seconds=data.get("timeout_seconds", 300),
            retry_count=data.get("retry_count", 3),
            on_error=data.get("on_error", "stop"),
        )
        if "status" in data:
            step.status = StepStatus(data["status"])
        if data.get("started_at"):
            step.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            step.completed_at = datetime.fromisoformat(data["completed_at"])
        step.error = data.get("error")
        return step


@dataclass
class Workflow:
    """Represents a complete workflow."""

    id: str
    name: str
    version: str
    description: str
    steps: List[WorkflowStep]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "pending"
    current_step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "current_step": self.current_step,
        }


class WorkflowEngine:
    """
    Engine for executing YAML-defined workflows.

    The WorkflowEngine supports:
    - Loading workflows from YAML files
    - Idempotent step execution
    - Checkpointing after each step
    - Resume from any checkpoint
    - Error handling and retry logic

    Example:
        >>> engine = WorkflowEngine(state_engine)
        >>> workflow = engine.load("workflow.yaml")
        >>> engine.execute(workflow)
    """

    def __init__(self, state_engine: StateEngine):
        """
        Initialize the WorkflowEngine.

        Args:
            state_engine: StateEngine for persistence.
        """
        self.state_engine = state_engine
        self._step_handlers: Dict[str, Callable] = {}

    def register_handler(self, step_name: str, handler: Callable) -> None:
        """
        Register a handler for a workflow step.

        Args:
            step_name: Name of the step.
            handler: Callable that executes the step.
        """
        self._step_handlers[step_name] = handler

    def load(self, workflow_path: str) -> Workflow:
        """
        Load a workflow from a YAML file.

        Args:
            workflow_path: Path to the workflow YAML file.

        Returns:
            Workflow instance.
        """
        path = Path(workflow_path)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        workflow_data = data.get("workflow", data)
        phases = data.get("phases", [])

        steps = []
        for i, phase in enumerate(phases):
            step = WorkflowStep(
                name=phase["name"],
                order=phase.get("order", i + 1),
                description=phase.get("description", ""),
                inputs=phase.get("inputs", []),
                outputs=phase.get("outputs", []),
                timeout_seconds=phase.get("timeout_seconds", 300),
                retry_count=phase.get("retry_count", 3),
                on_error=phase.get("on_error", "stop"),
            )
            steps.append(step)

        return Workflow(
            id=workflow_data.get("id", path.stem),
            name=workflow_data.get("name", path.stem),
            version=workflow_data.get("version", "1.0"),
            description=workflow_data.get("description", ""),
            steps=steps,
        )

    def execute(
        self,
        workflow: Workflow,
        context: Optional[Dict[str, Any]] = None,
        resume_from: Optional[int] = None,
    ) -> Workflow:
        """
        Execute a workflow.

        Args:
            workflow: The workflow to execute.
            context: Initial context data.
            resume_from: Step number to resume from (0-indexed).

        Returns:
            The executed workflow with updated status.
        """
        context = context or {}
        workflow.status = "running"
        workflow.updated_at = datetime.utcnow()

        start_step = resume_from if resume_from is not None else 0

        for i, step in enumerate(workflow.steps[start_step:], start=start_step):
            workflow.current_step = i

            # Check if step already completed
            if step.status == StepStatus.COMPLETED:
                continue

            # Execute the step
            try:
                step.status = StepStatus.RUNNING
                step.started_at = datetime.utcnow()

                # Create checkpoint before execution
                self._create_checkpoint(workflow, f"pre_step_{i}")

                # Execute step handler
                if step.name in self._step_handlers:
                    handler = self._step_handlers[step.name]
                    step.result = handler(step, context)
                else:
                    # Default handler - just mark as complete
                    step.result = {"status": "completed", "message": f"Step {step.name} executed"}

                step.status = StepStatus.COMPLETED
                step.completed_at = datetime.utcnow()

                # Create checkpoint after execution
                self._create_checkpoint(workflow, f"post_step_{i}")

            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)

                if step.on_error == "stop":
                    workflow.status = "failed"
                    break
                elif step.on_error == "skip":
                    step.status = StepStatus.SKIPPED
                    continue
                # retry is handled by caller

        # Check if all steps completed
        if all(s.status == StepStatus.COMPLETED for s in workflow.steps):
            workflow.status = "completed"
        elif any(s.status == StepStatus.FAILED for s in workflow.steps):
            workflow.status = "failed"

        workflow.updated_at = datetime.utcnow()
        return workflow

    def resume(self, workflow_id: str) -> Optional[Workflow]:
        """
        Resume a workflow from its last checkpoint.

        Args:
            workflow_id: The workflow ID to resume.

        Returns:
            The workflow if found, None otherwise.
        """
        checkpoints = self.state_engine.list_checkpoints(workflow_id)
        if not checkpoints:
            return None

        # Find the latest checkpoint
        latest = sorted(checkpoints)[-1]
        state = self.state_engine.load_checkpoint(workflow_id, latest)

        if not state:
            return None

        # Reconstruct workflow from state
        workflow_data = state.context.get("workflow")
        if not workflow_data:
            return None

        return self._workflow_from_state(workflow_data)

    def _create_checkpoint(self, workflow: Workflow, checkpoint_name: str) -> None:
        """Create a checkpoint for the workflow."""
        state = TaskState(
            task_id=workflow.id,
            task_description=workflow.description,
            status=workflow.status,
            current_step=workflow.current_step,
            created_at=workflow.created_at,
            updated_at=datetime.utcnow(),
            context={"workflow": workflow.to_dict()},
        )
        self.state_engine.create_checkpoint(state, checkpoint_name)

    def _workflow_from_state(self, data: Dict[str, Any]) -> Workflow:
        """Reconstruct a workflow from saved state."""
        steps = [WorkflowStep.from_dict(s) for s in data.get("steps", [])]

        workflow = Workflow(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            description=data["description"],
            steps=steps,
            status=data.get("status", "pending"),
            current_step=data.get("current_step", 0),
        )

        if data.get("created_at"):
            workflow.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            workflow.updated_at = datetime.fromisoformat(data["updated_at"])

        return workflow

    def get_status(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Get the current status of a workflow.

        Args:
            workflow: The workflow to check.

        Returns:
            Status dictionary.
        """
        completed = sum(1 for s in workflow.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in workflow.steps if s.status == StepStatus.FAILED)
        pending = sum(1 for s in workflow.steps if s.status == StepStatus.PENDING)

        return {
            "workflow_id": workflow.id,
            "status": workflow.status,
            "current_step": workflow.current_step,
            "total_steps": len(workflow.steps),
            "completed_steps": completed,
            "failed_steps": failed,
            "pending_steps": pending,
            "progress": completed / len(workflow.steps) if workflow.steps else 0,
        }
