"""Tests for exclusion patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from llm_context_collector.exclusions import (
    DEFAULT_MAX_FILE_SIZE,
    ExclusionConfig,
    is_excluded,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def default_config() -> ExclusionConfig:
    return ExclusionConfig()


class TestExclusionConfig:
    def test_default_has_expected_dirs(self) -> None:
        config = ExclusionConfig()
        assert ".git" in config.excluded_dirs
        assert "node_modules" in config.excluded_dirs
        assert "__pycache__" in config.excluded_dirs

    def test_default_has_expected_patterns(self) -> None:
        config = ExclusionConfig()
        assert "*.pyc" in config.excluded_patterns
        assert "*.lock" in config.excluded_patterns
        assert "*.png" in config.excluded_patterns

    def test_from_config_adds_additional(self) -> None:
        config = ExclusionConfig.from_config(additional=["*.log", "docs/generated/"])
        assert "*.log" in config.excluded_patterns
        assert "docs/generated" in config.excluded_dirs

    def test_from_config_removes_defaults(self) -> None:
        config = ExclusionConfig.from_config(remove_defaults=["*.svg"])
        assert "*.svg" not in config.excluded_patterns
        # Other defaults still present
        assert "*.png" in config.excluded_patterns

    def test_from_config_custom_max_size(self) -> None:
        config = ExclusionConfig.from_config(max_file_size=2_000_000)
        assert config.max_file_size == 2_000_000

    def test_default_max_size(self) -> None:
        config = ExclusionConfig()
        assert config.max_file_size == DEFAULT_MAX_FILE_SIZE


class TestIsExcluded:
    def test_excludes_pyc_file(self, tmp_path: Path, default_config: ExclusionConfig) -> None:
        f = tmp_path / "test.pyc"
        f.write_bytes(b"\x00")
        reason = is_excluded(str(f), default_config, str(tmp_path))
        assert reason is not None
        assert "*.pyc" in reason

    def test_excludes_file_in_excluded_dir(
        self, tmp_path: Path, default_config: ExclusionConfig
    ) -> None:
        d = tmp_path / "node_modules" / "pkg"
        d.mkdir(parents=True)
        f = d / "index.js"
        f.write_text("module.exports = {};", encoding="utf-8")
        reason = is_excluded(str(f), default_config, str(tmp_path))
        assert reason is not None
        assert "node_modules" in reason

    def test_allows_normal_file(self, tmp_path: Path, default_config: ExclusionConfig) -> None:
        f = tmp_path / "app.py"
        f.write_text("print('hello')", encoding="utf-8")
        reason = is_excluded(str(f), default_config, str(tmp_path))
        assert reason is None

    def test_excludes_large_file(self, tmp_path: Path) -> None:
        config = ExclusionConfig.from_config(max_file_size=100)
        f = tmp_path / "big.txt"
        f.write_text("x" * 200, encoding="utf-8")
        reason = is_excluded(str(f), config, str(tmp_path))
        assert reason is not None
        assert "too large" in reason

    def test_excludes_binary_file(self, tmp_path: Path, default_config: ExclusionConfig) -> None:
        f = tmp_path / "data.bin"
        f.write_bytes(b"\x00\x01\x02\xff\xfe\xfd" * 200)
        reason = is_excluded(str(f), default_config, str(tmp_path))
        assert reason is not None
        assert "binary" in reason
