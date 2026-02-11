"""Tests for the workspace query layer."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from geekcode.core.workspace_query import (
    detect_queries,
    run_query,
    gather_workspace_context,
    find_files_by_name,
    find_files_by_symbol,
    find_files_by_content,
    find_relevant_docs,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Shell query detection
# ═══════════════════════════════════════════════════════════════════════════════

class TestDetectQueries:
    """Tests for keyword → command detection."""

    def test_last_commit(self):
        matches = detect_queries("when was the last commit?")
        labels = [m[0] for m in matches]
        assert "Recent commits" in labels

    def test_recent_changes(self):
        matches = detect_queries("show me recent changes")
        labels = [m[0] for m in matches]
        assert "Recent commits" in labels

    def test_git_status(self):
        matches = detect_queries("what is the git status?")
        labels = [m[0] for m in matches]
        assert "Git status" in labels

    def test_uncommitted(self):
        matches = detect_queries("are there uncommitted files?")
        labels = [m[0] for m in matches]
        assert "Git status" in labels

    def test_git_diff(self):
        matches = detect_queries("show me the diff")
        labels = [m[0] for m in matches]
        assert "Git diff" in labels

    def test_what_changed(self):
        matches = detect_queries("what changed since yesterday?")
        labels = [m[0] for m in matches]
        assert "Git diff" in labels

    def test_current_branch(self):
        matches = detect_queries("which branch am I on?")
        labels = [m[0] for m in matches]
        assert "Git branch" in labels

    def test_list_branches(self):
        matches = detect_queries("show all branches")
        labels = [m[0] for m in matches]
        assert "Git branches" in labels

    def test_project_structure(self):
        matches = detect_queries("show the project structure")
        labels = [m[0] for m in matches]
        assert "Project structure" in labels

    def test_list_files(self):
        matches = detect_queries("list the files in this project")
        labels = [m[0] for m in matches]
        assert "Project structure" in labels

    def test_tags(self):
        matches = detect_queries("what is the latest version tag?")
        labels = [m[0] for m in matches]
        assert "Git tags" in labels

    def test_contributors(self):
        matches = detect_queries("who contributed to this project?")
        labels = [m[0] for m in matches]
        assert "Contributors" in labels

    def test_stash(self):
        matches = detect_queries("do I have any stashes?")
        labels = [m[0] for m in matches]
        assert "Git stash" in labels

    def test_no_match(self):
        matches = detect_queries("explain how the login module works")
        assert matches == []

    def test_no_match_coding_task(self):
        matches = detect_queries("add a new endpoint for user profile")
        assert matches == []

    def test_multiple_matches(self):
        matches = detect_queries("show me the git status and recent commits")
        labels = [m[0] for m in matches]
        assert "Git status" in labels
        assert "Recent commits" in labels

    def test_no_duplicate_labels(self):
        matches = detect_queries("show me the commit log and commit history")
        labels = [m[0] for m in matches]
        assert labels.count("Recent commits") == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Shell query execution
# ═══════════════════════════════════════════════════════════════════════════════

class TestRunQuery:
    """Tests for running shell commands."""

    def test_run_echo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = run_query(["echo", "hello"], Path(tmpdir))
            assert output == "hello"

    def test_run_timeout(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = run_query(["sleep", "30"], Path(tmpdir), timeout=1)
            assert "timed out" in output

    def test_run_command_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = run_query(["nonexistent_cmd_xyz"], Path(tmpdir))
            assert "not found" in output

    def test_run_truncates_long_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = ["python3", "-c", "print('x\\n' * 5000)"]
            output = run_query(cmd, Path(tmpdir))
            assert "more lines" in output


# ═══════════════════════════════════════════════════════════════════════════════
# File discovery
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindFilesByName:
    """Tests for extracting file references from task text."""

    def test_finds_explicit_py_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "agent.py").write_text("class Agent: pass")
            found = find_files_by_name("explain the code in agent.py", ws)
            assert len(found) == 1
            assert found[0].name == "agent.py"

    def test_finds_nested_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "src").mkdir()
            (ws / "src" / "main.go").write_text("package main")
            found = find_files_by_name("look at file src/main.go", ws)
            assert len(found) == 1

    def test_no_match_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            found = find_files_by_name("do something cool", Path(tmpdir))
            assert found == []

    def test_finds_yaml_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "config.yaml").write_text("key: value")
            found = find_files_by_name("read the config.yaml file", ws)
            assert len(found) == 1


class TestFindFilesBySymbol:
    """Tests for symbol-based code search."""

    def test_finds_python_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "utils.py").write_text("def calculate_score(x):\n    return x * 2\n")
            results = find_files_by_symbol("what does function calculate_score do?", ws)
            assert len(results) == 1
            assert results[0][1] == "calculate_score"

    def test_finds_python_class(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "models.py").write_text("class UserProfile:\n    pass\n")
            results = find_files_by_symbol("explain class UserProfile", ws)
            assert len(results) == 1
            assert results[0][1] == "UserProfile"

    def test_no_symbol_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = find_files_by_symbol("fix the bug", Path(tmpdir))
            assert results == []

    def test_ignores_pycache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            pycache = ws / "__pycache__"
            pycache.mkdir()
            (pycache / "utils.cpython-312.pyc").write_text("")
            (ws / "utils.py").write_text("def my_func():\n    pass\n")
            results = find_files_by_symbol("function my_func", ws)
            assert len(results) == 1
            assert "__pycache__" not in str(results[0][0])


class TestFindFilesByContent:
    """Tests for keyword-based file search (fallback)."""

    def test_scores_by_keyword_overlap(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "auth.py").write_text("def authenticate(user, password):\n    token = generate_jwt(user)\n    return token\n")
            (ws / "utils.py").write_text("def format_string(s):\n    return s.strip()\n")
            results = find_files_by_content("how does authentication work with JWT token", ws)
            assert len(results) >= 1
            # auth.py should score higher
            assert results[0][0].name == "auth.py"

    def test_returns_empty_for_stop_words_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "test.py").write_text("hello world")
            results = find_files_by_content("what does this have", ws)
            assert results == []


# ═══════════════════════════════════════════════════════════════════════════════
# Document search
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindRelevantDocs:
    """Tests for document discovery."""

    def test_finds_readme(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "README.md").write_text("# My Project\nSome description")
            docs = find_relevant_docs("what does the readme say?", ws)
            assert len(docs) == 1
            assert docs[0].name == "README.md"

    def test_finds_docs_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "docs").mkdir()
            (ws / "docs" / "guide.md").write_text("# Guide\nSetup instructions")
            docs = find_relevant_docs("read the documentation guide", ws)
            assert len(docs) >= 1

    def test_finds_changelog(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "CHANGELOG.md").write_text("# Changelog\n## v1.0.0\n- Initial release")
            docs = find_relevant_docs("show me the changelog", ws)
            assert len(docs) == 1

    def test_no_match_for_unrelated_query(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "README.md").write_text("Hello")
            docs = find_relevant_docs("fix the authentication bug", ws)
            assert docs == []


# ═══════════════════════════════════════════════════════════════════════════════
# Full pipeline (gather_workspace_context)
# ═══════════════════════════════════════════════════════════════════════════════

class TestGatherWorkspaceContext:
    """Tests for the full gather pipeline."""

    def test_returns_none_for_no_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # A task that doesn't match shell queries, file refs, symbols, or docs
            result = gather_workspace_context(
                "add a new endpoint for user profile", Path(tmpdir)
            )
            assert result is None

    def test_returns_context_for_git_query(self):
        """Test with a real git repo (the project itself)."""
        project_root = Path(__file__).resolve().parent.parent
        if not (project_root / ".git").exists():
            pytest.skip("Not in a git repo")

        result = gather_workspace_context(
            "when was the last commit?", project_root
        )
        assert result is not None
        assert "Recent commits" in result
        assert "```" in result

    def test_returns_multiple_sections(self):
        """Test that multiple matched queries produce multiple sections."""
        project_root = Path(__file__).resolve().parent.parent
        if not (project_root / ".git").exists():
            pytest.skip("Not in a git repo")

        result = gather_workspace_context(
            "show git status and recent commits", project_root
        )
        assert result is not None
        assert "Git status" in result
        assert "Recent commits" in result

    def test_reads_file_when_referenced(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "server.py").write_text("from flask import Flask\napp = Flask(__name__)\n")
            result = gather_workspace_context("explain the code in server.py", ws)
            assert result is not None
            assert "server.py" in result
            assert "Flask" in result

    def test_finds_symbol_in_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "math_utils.py").write_text("def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n")
            result = gather_workspace_context("explain function fibonacci", ws)
            assert result is not None
            assert "fibonacci" in result

    def test_reads_document(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "README.md").write_text("# My App\nThis app handles user authentication.\n")
            result = gather_workspace_context("what does the readme say about authentication?", ws)
            assert result is not None
            assert "README.md" in result
            assert "authentication" in result

    def test_fallback_content_search(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            (ws / "payment.py").write_text(
                "def process_payment(amount, currency):\n"
                "    stripe.charge(amount=amount, currency=currency)\n"
                "    return True\n"
            )
            result = gather_workspace_context(
                "explain how payment processing with stripe works", ws
            )
            assert result is not None
            assert "payment" in result.lower()
