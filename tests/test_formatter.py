"""Tests for Markdown output generation."""

from __future__ import annotations

import pytest

from context_collector.collector import CollectedFile
from context_collector.formatter import estimate_output_size, format_output


@pytest.fixture
def sample_files() -> list[CollectedFile]:
    return [
        CollectedFile(
            relative_path="src/app.py",
            absolute_path="/tmp/src/app.py",
            content='print("hello")\n',
            size=16,
            line_count=1,
        ),
        CollectedFile(
            relative_path="src/models.py",
            absolute_path="/tmp/src/models.py",
            content="class User:\n    pass\n",
            size=21,
            line_count=2,
        ),
    ]


class TestFormatOutput:
    def test_includes_topic_name(self, sample_files: list[CollectedFile]) -> None:
        output = format_output(sample_files, repo_name="my-repo", topic_name="auth")
        assert "# Context: auth" in output

    def test_custom_selection_when_no_topic(
        self, sample_files: list[CollectedFile]
    ) -> None:
        output = format_output(sample_files, repo_name="my-repo")
        assert "# Context: Custom Selection" in output

    def test_includes_topic_description(
        self, sample_files: list[CollectedFile]
    ) -> None:
        output = format_output(
            sample_files,
            repo_name="my-repo",
            topic_name="auth",
            topic_description="Auth flow",
        )
        assert "Auth flow" in output

    def test_includes_repo_name(self, sample_files: list[CollectedFile]) -> None:
        output = format_output(sample_files, repo_name="my-repo")
        assert "my-repo" in output

    def test_includes_file_count(self, sample_files: list[CollectedFile]) -> None:
        output = format_output(sample_files, repo_name="my-repo")
        assert "**Files:** 2" in output

    def test_includes_table_of_contents(
        self, sample_files: list[CollectedFile]
    ) -> None:
        output = format_output(sample_files, repo_name="my-repo")
        assert "## Table of Contents" in output
        assert "src/app.py" in output
        assert "src/models.py" in output

    def test_no_toc_when_disabled(self, sample_files: list[CollectedFile]) -> None:
        output = format_output(sample_files, repo_name="my-repo", include_toc=False)
        assert "## Table of Contents" not in output

    def test_includes_file_contents(self, sample_files: list[CollectedFile]) -> None:
        output = format_output(sample_files, repo_name="my-repo")
        assert '```python\nprint("hello")\n```' in output
        assert "```python\nclass User:\n    pass\n```" in output

    def test_includes_file_headers(self, sample_files: list[CollectedFile]) -> None:
        output = format_output(sample_files, repo_name="my-repo")
        assert "## src/app.py" in output
        assert "## src/models.py" in output

    def test_includes_separators(self, sample_files: list[CollectedFile]) -> None:
        output = format_output(sample_files, repo_name="my-repo")
        assert "---" in output

    def test_language_detection(self) -> None:
        files = [
            CollectedFile(
                relative_path="config.yml",
                absolute_path="/tmp/config.yml",
                content="key: value\n",
                size=11,
                line_count=1,
            ),
        ]
        output = format_output(files, repo_name="my-repo")
        assert "```yaml\n" in output


class TestEstimateOutputSize:
    def test_estimate_is_reasonable(self, sample_files: list[CollectedFile]) -> None:
        estimate = estimate_output_size(sample_files)
        content_size = sum(f.size for f in sample_files)
        assert estimate > content_size  # Should include overhead
        assert estimate < content_size + 5000  # Overhead is bounded

    def test_empty_files_has_minimal_estimate(self) -> None:
        estimate = estimate_output_size([])
        assert estimate == 500  # Just the document header overhead
