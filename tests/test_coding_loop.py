"""Tests for the agentic coding loop."""

import json
import textwrap

import pytest

from geekcode.core.coding_loop import CodingLoop, Edit, is_coding_task


# ---------------------------------------------------------------------------
# is_coding_task heuristic
# ---------------------------------------------------------------------------


class TestIsCodingTask:
    def test_fix_bug(self):
        assert is_coding_task("Fix the bug in user_service.py") is True

    def test_add_tests(self):
        assert is_coding_task("Add unit tests for the login handler") is True

    def test_refactor_class(self):
        assert is_coding_task("Refactor the UserModel class") is True

    def test_implement_endpoint(self):
        assert is_coding_task("Implement the /api/users endpoint") is True

    def test_research_not_coding(self):
        assert is_coding_task("Explain how caching works") is False

    def test_analysis_not_coding(self):
        assert is_coding_task("What is the architecture of this project?") is False

    def test_verb_with_file_ref(self):
        assert is_coding_task("Fix auth.py") is True

    def test_generic_question(self):
        assert is_coding_task("How does the database connection pool work?") is False


# ---------------------------------------------------------------------------
# Edit parsing
# ---------------------------------------------------------------------------


class TestParseEdits:
    def setup_method(self):
        # CodingLoop needs workspace/geekcode_dir but parsing is stateless
        self.loop = CodingLoop.__new__(CodingLoop)

    def test_parse_single_edit(self):
        response = textwrap.dedent('''
            Here is the fix:

            <<<EDIT file="src/utils.py">>>
            <<<OLD>>>
            def add(a, b):
                return a - b
            <<<NEW>>>
            def add(a, b):
                return a + b
            <<<END>>>
        ''')
        edits = self.loop._parse_edits(response)
        assert len(edits) == 1
        assert edits[0].file_path == "src/utils.py"
        assert "return a - b" in edits[0].old_content
        assert "return a + b" in edits[0].new_content
        assert edits[0].is_create is False

    def test_parse_multiple_edits(self):
        response = textwrap.dedent('''
            <<<EDIT file="a.py">>>
            <<<OLD>>>
            x = 1
            <<<NEW>>>
            x = 2
            <<<END>>>

            <<<EDIT file="b.py">>>
            <<<OLD>>>
            y = 3
            <<<NEW>>>
            y = 4
            <<<END>>>
        ''')
        edits = self.loop._parse_edits(response)
        assert len(edits) == 2
        assert edits[0].file_path == "a.py"
        assert edits[1].file_path == "b.py"

    def test_parse_create(self):
        response = textwrap.dedent('''
            <<<CREATE file="tests/test_new.py">>>
            def test_hello():
                assert True
            <<<END>>>
        ''')
        edits = self.loop._parse_edits(response)
        assert len(edits) == 1
        assert edits[0].file_path == "tests/test_new.py"
        assert edits[0].is_create is True
        assert "def test_hello" in edits[0].new_content

    def test_parse_mixed_edit_and_create(self):
        response = textwrap.dedent('''
            <<<EDIT file="src/main.py">>>
            <<<OLD>>>
            pass
            <<<NEW>>>
            return 42
            <<<END>>>

            <<<CREATE file="src/helper.py">>>
            def helper():
                return True
            <<<END>>>
        ''')
        edits = self.loop._parse_edits(response)
        assert len(edits) == 2
        assert edits[0].is_create is False
        assert edits[1].is_create is True

    def test_parse_no_edits(self):
        edits = self.loop._parse_edits("I cannot make changes to this file.")
        assert edits == []


# ---------------------------------------------------------------------------
# Apply edits
# ---------------------------------------------------------------------------


class TestApplyEdits:
    def setup_method(self):
        self.loop = CodingLoop.__new__(CodingLoop)

    def test_apply_edit(self, tmp_path):
        self.loop.workspace = tmp_path

        target = tmp_path / "src" / "app.py"
        target.parent.mkdir(parents=True)
        target.write_text("def greet():\n    return 'hello'\n")

        edits = [Edit(
            file_path="src/app.py",
            old_content="return 'hello'",
            new_content="return 'world'",
        )]

        applied = self.loop._apply_edits(edits)
        assert len(applied) == 1
        assert applied[0]["applied"] is True

        assert "return 'world'" in target.read_text()

    def test_apply_create(self, tmp_path):
        self.loop.workspace = tmp_path

        edits = [Edit(
            file_path="new_dir/new_file.py",
            old_content="",
            new_content="print('created')\n",
            is_create=True,
        )]

        applied = self.loop._apply_edits(edits)
        assert applied[0]["applied"] is True
        assert applied[0]["action"] == "create"

        created = tmp_path / "new_dir" / "new_file.py"
        assert created.exists()
        assert "print('created')" in created.read_text()

    def test_apply_edit_file_not_found(self, tmp_path):
        self.loop.workspace = tmp_path

        edits = [Edit(
            file_path="nonexistent.py",
            old_content="old",
            new_content="new",
        )]

        applied = self.loop._apply_edits(edits)
        assert applied[0]["applied"] is False
        assert "not found" in applied[0]["error"]

    def test_apply_edit_old_content_not_found(self, tmp_path):
        self.loop.workspace = tmp_path

        target = tmp_path / "file.py"
        target.write_text("actual content here\n")

        edits = [Edit(
            file_path="file.py",
            old_content="this does not exist",
            new_content="replacement",
        )]

        applied = self.loop._apply_edits(edits)
        assert applied[0]["applied"] is False
        assert "not found" in applied[0]["error"]


# ---------------------------------------------------------------------------
# Test framework detection
# ---------------------------------------------------------------------------


class TestDetectTestCommand:
    def setup_method(self):
        self.loop = CodingLoop.__new__(CodingLoop)

    def test_detect_pytest_ini(self, tmp_path):
        self.loop.workspace = tmp_path
        (tmp_path / "pytest.ini").write_text("[pytest]\n")
        assert self.loop._detect_test_command(["app.py"]) == "python -m pytest"

    def test_detect_pyproject_toml_pytest(self, tmp_path):
        self.loop.workspace = tmp_path
        (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
        assert self.loop._detect_test_command(["app.py"]) == "python -m pytest"

    def test_detect_npm_test(self, tmp_path):
        self.loop.workspace = tmp_path
        pkg = {"scripts": {"test": "jest"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg))
        assert self.loop._detect_test_command(["app.js"]) == "npm test"

    def test_detect_go_test(self, tmp_path):
        self.loop.workspace = tmp_path
        (tmp_path / "go.mod").write_text("module example.com/app\n")
        assert self.loop._detect_test_command(["main.go"]) == "go test ./..."

    def test_detect_cargo_test(self, tmp_path):
        self.loop.workspace = tmp_path
        (tmp_path / "Cargo.toml").write_text("[package]\nname = 'app'\n")
        assert self.loop._detect_test_command(["main.rs"]) == "cargo test"

    def test_detect_makefile_test(self, tmp_path):
        self.loop.workspace = tmp_path
        (tmp_path / "Makefile").write_text("test:\n\tpytest\n")
        assert self.loop._detect_test_command(["app.c"]) == "make test"

    def test_fallback_pytest_for_py_files(self, tmp_path):
        self.loop.workspace = tmp_path
        assert self.loop._detect_test_command(["app.py"]) == "python -m pytest"

    def test_no_detection_for_unknown(self, tmp_path):
        self.loop.workspace = tmp_path
        assert self.loop._detect_test_command(["readme.txt"]) is None


# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------


class TestRunTests:
    def setup_method(self):
        self.loop = CodingLoop.__new__(CodingLoop)

    def test_run_tests_pass(self, tmp_path):
        self.loop.workspace = tmp_path
        passed, output = self.loop._run_tests("python -c \"print('ok')\"")
        assert passed is True
        assert "ok" in output

    def test_run_tests_fail(self, tmp_path):
        self.loop.workspace = tmp_path
        passed, output = self.loop._run_tests("python -c \"raise SystemExit(1)\"")
        assert passed is False

    def test_run_tests_timeout(self, tmp_path):
        self.loop.workspace = tmp_path
        passed, output = self.loop._run_tests("sleep 10", timeout=1)
        assert passed is False
        assert "timed out" in output.lower()


# ---------------------------------------------------------------------------
# Checkpoint persistence
# ---------------------------------------------------------------------------


class TestCheckpoint:
    def test_save_and_load(self, tmp_path):
        geekcode_dir = tmp_path / ".geekcode"
        geekcode_dir.mkdir()
        loop = CodingLoop(tmp_path, geekcode_dir)

        state = {
            "task": "Fix the bug",
            "files": ["app.py"],
            "iteration": 2,
            "status": "running",
        }
        loop._checkpoint(state)

        loaded = loop._load_checkpoint()
        assert loaded is not None
        assert loaded["task"] == "Fix the bug"
        assert loaded["iteration"] == 2
        assert loaded["status"] == "running"

    def test_load_no_checkpoint(self, tmp_path):
        geekcode_dir = tmp_path / ".geekcode"
        geekcode_dir.mkdir()
        loop = CodingLoop(tmp_path, geekcode_dir)

        assert loop._load_checkpoint() is None

    def test_reset(self, tmp_path):
        geekcode_dir = tmp_path / ".geekcode"
        geekcode_dir.mkdir()
        loop = CodingLoop(tmp_path, geekcode_dir)

        loop._checkpoint({"task": "test", "status": "running"})
        assert loop.reset() is True
        assert loop._load_checkpoint() is None

    def test_reset_no_checkpoint(self, tmp_path):
        geekcode_dir = tmp_path / ".geekcode"
        geekcode_dir.mkdir()
        loop = CodingLoop(tmp_path, geekcode_dir)

        assert loop.reset() is False
