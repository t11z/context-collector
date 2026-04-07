"""Tests for configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from llm_context_collector.config import (
    ConfigError,
    ProjectConfig,
    find_config_file,
    load_config,
)


@pytest.fixture
def sample_config_path() -> Path:
    return Path(__file__).parent / "fixtures" / "sample-config.toml"


@pytest.fixture
def sample_repo_path() -> Path:
    return Path(__file__).parent / "fixtures" / "sample-repo"


class TestLoadConfig:
    def test_loads_valid_config(self, sample_config_path: Path) -> None:
        config = load_config(sample_config_path)
        assert isinstance(config, ProjectConfig)
        assert "api" in config.topics
        assert "models" in config.topics

    def test_topic_has_correct_fields(self, sample_config_path: Path) -> None:
        config = load_config(sample_config_path)
        api = config.topics["api"]
        assert api.name == "api"
        assert api.description == "API endpoints and routing"
        assert "src/app.py" in api.paths
        assert "src/routes/" in api.paths

    def test_exclusion_overrides(self, sample_config_path: Path) -> None:
        config = load_config(sample_config_path)
        assert "*.log" in config.exclusion_config.excluded_patterns

    def test_missing_file_raises_error(self) -> None:
        with pytest.raises(ConfigError, match="not found"):
            load_config("/nonexistent/path.toml")

    def test_invalid_toml_raises_error(self, tmp_path: Path) -> None:
        bad_toml = tmp_path / "bad.toml"
        bad_toml.write_text("this is not [valid toml", encoding="utf-8")
        with pytest.raises(ConfigError, match="Invalid TOML"):
            load_config(bad_toml)

    def test_topic_missing_paths_raises_error(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".llm-context-collector.toml"
        config_file.write_text(
            '[topics.broken]\ndescription = "missing paths"\n',
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="missing 'paths'"):
            load_config(config_file)

    def test_topic_paths_not_list_raises_error(self, tmp_path: Path) -> None:
        config_file = tmp_path / ".llm-context-collector.toml"
        config_file.write_text(
            '[topics.broken]\npaths = "not-a-list"\n',
            encoding="utf-8",
        )
        with pytest.raises(ConfigError, match="must be a list"):
            load_config(config_file)


class TestFindConfigFile:
    def test_finds_config_in_directory(self, sample_repo_path: Path) -> None:
        result = find_config_file(str(sample_repo_path))
        assert result is not None
        assert result.name == ".llm-context-collector.toml"

    def test_finds_config_in_parent(self, sample_repo_path: Path) -> None:
        child_dir = sample_repo_path / "src" / "routes"
        result = find_config_file(str(child_dir))
        assert result is not None
        assert result.name == ".llm-context-collector.toml"

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        result = find_config_file(str(tmp_path))
        assert result is None
