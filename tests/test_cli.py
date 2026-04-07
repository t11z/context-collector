"""Integration tests for the CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from llm_context_collector.cli import main

SAMPLE_REPO = Path(__file__).parent / "fixtures" / "sample-repo"


class TestCLIIntegration:
    """Integration tests that run the CLI against the sample repo."""

    def test_collect_topic(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        main(["api", "-o", str(tmp_path / "output.md")])
        output = (tmp_path / "output.md").read_text(encoding="utf-8")
        assert "# Context: api" in output
        assert "src/app.py" in output
        assert "create_app" in output

    def test_collect_paths(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        main(["--paths", "src/models.py", "-o", str(tmp_path / "output.md")])
        output = (tmp_path / "output.md").read_text(encoding="utf-8")
        assert "# Context: Custom Selection" in output
        assert "class User" in output

    def test_dry_run(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        main(["api", "--dry-run"])
        captured = capsys.readouterr()
        assert "Would include" in captured.out
        assert "src/app.py" in captured.out

    def test_list_topics(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        main(["--list-topics"])
        captured = capsys.readouterr()
        assert "api" in captured.out
        assert "models" in captured.out
        assert "API endpoints" in captured.out

    def test_stdout_output(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        main(["models", "-o", "-"])
        captured = capsys.readouterr()
        assert "# Context: models" in captured.out
        assert "class User" in captured.out

    def test_no_toc(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        main(["api", "--no-toc", "-o", str(tmp_path / "output.md")])
        output = (tmp_path / "output.md").read_text(encoding="utf-8")
        assert "## Table of Contents" not in output

    def test_unknown_topic_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        with pytest.raises(SystemExit) as exc_info:
            main(["nonexistent"])
        assert exc_info.value.code == 1

    def test_no_args_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 1

    def test_topic_and_paths_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        with pytest.raises(SystemExit) as exc_info:
            main(["api", "--paths", "src/"])
        assert exc_info.value.code == 1

    def test_quiet_mode(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        main(["api", "-q", "-o", str(tmp_path / "output.md")])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "llm-context-collector" in captured.out

    def test_default_output_name_for_topic(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.chdir(SAMPLE_REPO)
        # Use a temporary output dir to avoid polluting fixtures
        output_file = SAMPLE_REPO / "context-api.md"
        try:
            main(["api"])
            assert output_file.exists()
            content = output_file.read_text(encoding="utf-8")
            assert "# Context: api" in content
        finally:
            if output_file.exists():
                output_file.unlink()


class TestCLIModule:
    """Test that the tool can be invoked as a Python module."""

    def test_python_m_invocation(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "llm_context_collector", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "llm-context-collector" in result.stdout
