"""Tests for the state engine."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from geekcode.state.engine import StateEngine, TaskState


class TestTaskState:
    """Tests for TaskState dataclass."""

    def test_create_task_state(self):
        """Test creating a TaskState."""
        state = TaskState(
            task_id="test-123",
            task_description="Test task",
            status="pending",
            current_step=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        assert state.task_id == "test-123"
        assert state.status == "pending"
        assert state.current_step == 1
        assert state.completed_steps == []

    def test_to_dict(self):
        """Test converting TaskState to dictionary."""
        now = datetime.utcnow()
        state = TaskState(
            task_id="test-123",
            task_description="Test task",
            status="running",
            current_step=2,
            created_at=now,
            updated_at=now,
            model="gpt-4",
            completed_steps=["step1"],
        )

        data = state.to_dict()

        assert data["task_id"] == "test-123"
        assert data["status"] == "running"
        assert data["model"] == "gpt-4"
        assert data["completed_steps"] == ["step1"]
        assert data["created_at"] == now.isoformat()

    def test_from_dict(self):
        """Test creating TaskState from dictionary."""
        now = datetime.utcnow()
        data = {
            "task_id": "test-456",
            "task_description": "Another test",
            "status": "completed",
            "current_step": 3,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "model": "claude-3",
            "completed_steps": ["a", "b", "c"],
        }

        state = TaskState.from_dict(data)

        assert state.task_id == "test-456"
        assert state.status == "completed"
        assert state.model == "claude-3"
        assert len(state.completed_steps) == 3


class TestStateEngine:
    """Tests for StateEngine."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def engine(self, temp_dir):
        """Create a StateEngine with temporary storage."""
        return StateEngine(state_dir=temp_dir)

    def test_save_and_load(self, engine):
        """Test saving and loading state."""
        state = TaskState(
            task_id="save-test",
            task_description="Test save",
            status="running",
            current_step=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Save
        path = engine.save(state)
        assert path.exists()

        # Load
        loaded = engine.load("save-test")
        assert loaded is not None
        assert loaded.task_id == "save-test"
        assert loaded.status == "running"

    def test_load_nonexistent(self, engine):
        """Test loading a state that doesn't exist."""
        result = engine.load("nonexistent")
        assert result is None

    def test_load_latest(self, engine):
        """Test loading the most recent state."""
        # Create multiple states
        for i in range(3):
            state = TaskState(
                task_id=f"task-{i}",
                task_description=f"Task {i}",
                status="running" if i == 2 else "completed",
                current_step=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            engine.save(state)

        # Load latest should return the running task
        latest = engine.load_latest()
        assert latest is not None
        assert latest.status == "running"

    def test_list_resumable(self, engine):
        """Test listing resumable tasks."""
        # Create tasks with various statuses
        for status in ["pending", "running", "completed", "paused"]:
            state = TaskState(
                task_id=f"task-{status}",
                task_description=f"Task {status}",
                status=status,
                current_step=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            engine.save(state)

        resumable = engine.list_resumable()

        # Should only include pending, running, and paused
        assert len(resumable) == 3
        statuses = [t.status for t in resumable]
        assert "completed" not in statuses

    def test_delete(self, engine):
        """Test deleting a state."""
        state = TaskState(
            task_id="delete-test",
            task_description="To be deleted",
            status="running",
            current_step=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        engine.save(state)

        # Verify it exists
        assert engine.load("delete-test") is not None

        # Delete
        result = engine.delete("delete-test")
        assert result is True

        # Verify it's gone
        assert engine.load("delete-test") is None

    def test_checkpoint(self, engine):
        """Test creating and loading checkpoints."""
        state = TaskState(
            task_id="checkpoint-test",
            task_description="Checkpoint test",
            status="running",
            current_step=2,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Create checkpoint
        checkpoint_path = engine.create_checkpoint(state, "phase_1")
        assert checkpoint_path.exists()

        # Load checkpoint
        loaded = engine.load_checkpoint("checkpoint-test", "phase_1")
        assert loaded is not None
        assert loaded.current_step == 2

    def test_list_checkpoints(self, engine):
        """Test listing checkpoints for a task."""
        state = TaskState(
            task_id="multi-checkpoint",
            task_description="Multiple checkpoints",
            status="running",
            current_step=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Create multiple checkpoints
        engine.create_checkpoint(state, "start")
        state.current_step = 2
        engine.create_checkpoint(state, "middle")
        state.current_step = 3
        engine.create_checkpoint(state, "end")

        checkpoints = engine.list_checkpoints("multi-checkpoint")
        assert len(checkpoints) == 3
        assert "start" in checkpoints
        assert "middle" in checkpoints
        assert "end" in checkpoints
