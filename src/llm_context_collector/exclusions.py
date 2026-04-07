"""Default exclusion patterns and override logic."""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass, field

# Directories that are always excluded by default
DEFAULT_EXCLUDED_DIRS: set[str] = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
    ".next",
    ".nuxt",
}

# File patterns excluded by default (glob-style)
DEFAULT_EXCLUDED_PATTERNS: set[str] = {
    "*.pyc",
    "*.pyo",
    "*.o",
    "*.so",
    "*.dll",
    "*.exe",
    "*.class",
    "*.lock",
    "package-lock.json",
    "yarn.lock",
    "Pipfile.lock",
    "poetry.lock",
    "Cargo.lock",
    "*.min.js",
    "*.min.css",
    "*.map",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.webp",
    "*.ico",
    "*.svg",
    "*.pdf",
    "*.zip",
    "*.tar",
    "*.gz",
}

DEFAULT_MAX_FILE_SIZE: int = 1_048_576  # 1 MB


@dataclass
class ExclusionConfig:
    """Resolved exclusion configuration combining defaults and user overrides."""

    excluded_dirs: set[str] = field(default_factory=lambda: set(DEFAULT_EXCLUDED_DIRS))
    excluded_patterns: set[str] = field(default_factory=lambda: set(DEFAULT_EXCLUDED_PATTERNS))
    max_file_size: int = DEFAULT_MAX_FILE_SIZE

    @classmethod
    def from_config(
        cls,
        additional: list[str] | None = None,
        remove_defaults: list[str] | None = None,
        max_file_size: int | None = None,
    ) -> ExclusionConfig:
        """Build an ExclusionConfig from user-provided overrides.

        Args:
            additional: Extra patterns to exclude.
            remove_defaults: Default patterns to remove (e.g., to allow *.svg).
            max_file_size: Override for the maximum file size in bytes.
        """
        dirs = set(DEFAULT_EXCLUDED_DIRS)
        patterns = set(DEFAULT_EXCLUDED_PATTERNS)

        if remove_defaults:
            for pattern in remove_defaults:
                dirs.discard(pattern.rstrip("/"))
                patterns.discard(pattern)

        if additional:
            for pattern in additional:
                if pattern.endswith("/"):
                    dirs.add(pattern.rstrip("/"))
                else:
                    patterns.add(pattern)

        return cls(
            excluded_dirs=dirs,
            excluded_patterns=patterns,
            max_file_size=max_file_size if max_file_size is not None else DEFAULT_MAX_FILE_SIZE,
        )


def is_excluded(
    filepath: str,
    config: ExclusionConfig,
    base_dir: str,
) -> str | None:
    """Check if a file should be excluded.

    Args:
        filepath: Absolute or relative path to the file.
        config: The exclusion configuration to apply.
        base_dir: The base directory for resolving relative paths.

    Returns:
        A reason string if excluded, or None if the file should be included.
    """
    rel_path = os.path.relpath(filepath, base_dir)
    parts = rel_path.replace("\\", "/").split("/")
    filename = parts[-1]

    # Check directory exclusions
    for part in parts[:-1]:
        if part in config.excluded_dirs:
            return f"excluded directory: {part}/"

    # Check pattern exclusions
    for pattern in config.excluded_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return f"excluded pattern: {pattern}"
        # Also check against relative path for path-based patterns
        if "/" in pattern and fnmatch.fnmatch(rel_path, pattern):
            return f"excluded pattern: {pattern}"

    # Check file size
    try:
        size = os.path.getsize(filepath)
        if size > config.max_file_size:
            return f"file too large: {size} bytes (max {config.max_file_size})"
    except OSError:
        return "cannot stat file"

    # Check if file is valid UTF-8
    try:
        with open(filepath, encoding="utf-8") as f:
            f.read(1024)  # Read a small chunk to validate encoding
    except (UnicodeDecodeError, OSError):
        return "binary or non-UTF-8 file"

    return None
