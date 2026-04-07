"""Configuration file loading and validation."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[import-not-found]

from context_collector.exclusions import ExclusionConfig


@dataclass
class TopicConfig:
    """A single topic definition from the config file."""

    name: str
    description: str
    paths: list[str]


@dataclass
class ProjectConfig:
    """Parsed and validated project configuration."""

    topics: dict[str, TopicConfig] = field(default_factory=dict)
    exclusion_config: ExclusionConfig = field(default_factory=ExclusionConfig)


class ConfigError(Exception):
    """Raised when the configuration file is invalid or cannot be loaded."""


def find_config_file(start_dir: str | None = None) -> Path | None:
    """Search for .context-collector.toml starting from start_dir, walking up to root.

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to the config file, or None if not found.
    """
    current = Path(start_dir) if start_dir else Path.cwd()
    current = current.resolve()

    while True:
        candidate = current / ".context-collector.toml"
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_config(config_path: str | Path) -> ProjectConfig:
    """Load and validate a configuration file.

    Args:
        config_path: Path to the .context-collector.toml file.

    Returns:
        A validated ProjectConfig.

    Raises:
        ConfigError: If the file cannot be read or is invalid.
    """
    config_path = Path(config_path)

    if not config_path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            raw = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"Invalid TOML in {config_path}: {e}") from e

    return _parse_config(raw)


def _parse_config(raw: dict[str, Any]) -> ProjectConfig:
    """Parse raw TOML data into a ProjectConfig."""
    topics: dict[str, TopicConfig] = {}

    raw_topics = raw.get("topics", {})
    if not isinstance(raw_topics, dict):
        raise ConfigError("'topics' must be a table")

    for name, topic_data in raw_topics.items():
        if not isinstance(topic_data, dict):
            raise ConfigError(f"Topic '{name}' must be a table")

        paths = topic_data.get("paths")
        if paths is None:
            raise ConfigError(f"Topic '{name}' is missing 'paths'")
        if not isinstance(paths, list):
            raise ConfigError(f"Topic '{name}': 'paths' must be a list")
        for i, p in enumerate(paths):
            if not isinstance(p, str):
                raise ConfigError(f"Topic '{name}': paths[{i}] must be a string")

        description = topic_data.get("description", "")
        if not isinstance(description, str):
            raise ConfigError(f"Topic '{name}': 'description' must be a string")

        topics[name] = TopicConfig(name=name, description=description, paths=paths)

    # Parse exclusions
    raw_exclusions = raw.get("exclusions", {})
    if not isinstance(raw_exclusions, dict):
        raise ConfigError("'exclusions' must be a table")

    additional = raw_exclusions.get("additional")
    remove_defaults = raw_exclusions.get("remove_defaults")
    max_file_size = raw_exclusions.get("max_file_size")

    if additional is not None and not isinstance(additional, list):
        raise ConfigError("'exclusions.additional' must be a list")
    if remove_defaults is not None and not isinstance(remove_defaults, list):
        raise ConfigError("'exclusions.remove_defaults' must be a list")
    if max_file_size is not None and not isinstance(max_file_size, int):
        raise ConfigError("'exclusions.max_file_size' must be an integer")

    exclusion_config = ExclusionConfig.from_config(
        additional=additional,
        remove_defaults=remove_defaults,
        max_file_size=max_file_size,
    )

    return ProjectConfig(topics=topics, exclusion_config=exclusion_config)


def get_repo_name() -> str:
    """Get the repository name from git remote or fall back to directory name."""
    try:
        # Try to read git remote
        git_config = Path.cwd() / ".git" / "config"
        if git_config.is_file():
            with open(git_config, encoding="utf-8") as f:
                content = f.read()
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("url = "):
                    url = line.split("=", 1)[1].strip()
                    # Handle SSH and HTTPS URLs
                    name = url.rstrip("/").rsplit("/", 1)[-1]
                    if name.endswith(".git"):
                        name = name[:-4]
                    return name
    except OSError:
        pass

    return os.path.basename(os.getcwd())
