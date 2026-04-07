"""Tests for the file collector."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_context_collector.collector import resolve_paths, resolve_topic
from llm_context_collector.config import TopicConfig
from llm_context_collector.exclusions import ExclusionConfig


@pytest.fixture
def sample_repo() -> Path:
    return Path(__file__).parent / "fixtures" / "sample-repo"


@pytest.fixture
def default_exclusions() -> ExclusionConfig:
    return ExclusionConfig()


class TestResolvePaths:
    def test_collects_single_file(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["src/app.py"], str(sample_repo), default_exclusions
        )
        assert len(files) == 1
        assert files[0].relative_path == "src/app.py"
        assert "create_app" in files[0].content

    def test_collects_directory(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["src/routes/"], str(sample_repo), default_exclusions
        )
        assert len(files) >= 2
        paths = [f.relative_path for f in files]
        assert any("auth.py" in p for p in paths)
        assert any("users.py" in p for p in paths)

    def test_collects_glob_pattern(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["src/**/*.py"], str(sample_repo), default_exclusions
        )
        assert len(files) >= 3  # app.py, models.py, routes/*.py

    def test_deduplicates_files(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["src/app.py", "src/app.py"], str(sample_repo), default_exclusions
        )
        assert len(files) == 1

    def test_sorts_by_path(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["src/"], str(sample_repo), default_exclusions
        )
        paths = [f.relative_path for f in files]
        assert paths == sorted(paths)

    def test_no_matches_returns_empty(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["nonexistent/"], str(sample_repo), default_exclusions
        )
        assert len(files) == 0

    def test_collected_file_has_line_count(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["src/app.py"], str(sample_repo), default_exclusions
        )
        assert files[0].line_count > 0

    def test_collected_file_has_size(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        files, _ = resolve_paths(
            ["src/app.py"], str(sample_repo), default_exclusions
        )
        assert files[0].size > 0


class TestResolveTopic:
    def test_resolves_api_topic(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        topic = TopicConfig(
            name="api",
            description="API endpoints",
            paths=["src/app.py", "src/routes/"],
        )
        files, _ = resolve_topic(topic, str(sample_repo), default_exclusions)
        assert len(files) >= 3
        paths = [f.relative_path for f in files]
        assert "src/app.py" in paths

    def test_resolves_models_topic(
        self, sample_repo: Path, default_exclusions: ExclusionConfig
    ) -> None:
        topic = TopicConfig(
            name="models",
            description="Data models",
            paths=["src/models.py"],
        )
        files, _ = resolve_topic(topic, str(sample_repo), default_exclusions)
        assert len(files) == 1
        assert files[0].relative_path == "src/models.py"
