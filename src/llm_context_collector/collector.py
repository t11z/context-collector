"""Core logic: resolve paths, filter files, read contents."""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from llm_context_collector.exclusions import ExclusionConfig, is_excluded

if TYPE_CHECKING:
    from llm_context_collector.config import TopicConfig


@dataclass
class CollectedFile:
    """A single file that has been collected."""

    relative_path: str
    absolute_path: str
    content: str
    size: int
    line_count: int


def resolve_paths(
    path_patterns: list[str],
    base_dir: str,
    exclusion_config: ExclusionConfig,
    verbose: bool = False,
) -> tuple[list[CollectedFile], list[str]]:
    """Resolve path patterns to collected files.

    Args:
        path_patterns: List of file paths, directory paths, or glob patterns.
        base_dir: The base directory to resolve relative paths against.
        exclusion_config: Exclusion rules to apply.
        verbose: If True, collect verbose messages about skipped files.

    Returns:
        A tuple of (collected files sorted by path, verbose messages).
    """
    messages: list[str] = []
    seen: set[str] = set()
    files: list[CollectedFile] = []

    for pattern in path_patterns:
        full_pattern = os.path.join(base_dir, pattern)

        # If it's a directory, collect all files recursively
        if os.path.isdir(full_pattern):
            _collect_directory(
                full_pattern, base_dir, exclusion_config, files, seen, messages, verbose
            )
            continue

        # Try glob expansion
        matches = sorted(glob.glob(full_pattern, recursive=True))
        if matches:
            for match in matches:
                if os.path.isdir(match):
                    _collect_directory(
                        match, base_dir, exclusion_config, files, seen, messages, verbose
                    )
                elif os.path.isfile(match):
                    _collect_file(
                        match, base_dir, exclusion_config, files, seen, messages, verbose
                    )
            continue

        # If it's a direct file path that exists
        if os.path.isfile(full_pattern):
            _collect_file(full_pattern, base_dir, exclusion_config, files, seen, messages, verbose)
            continue

        if verbose:
            messages.append(f"  No matches for pattern: {pattern}")

    files.sort(key=lambda f: f.relative_path)
    return files, messages


def resolve_topic(
    topic: TopicConfig,
    base_dir: str,
    exclusion_config: ExclusionConfig,
    verbose: bool = False,
) -> tuple[list[CollectedFile], list[str]]:
    """Resolve a topic to collected files.

    Args:
        topic: The topic configuration.
        base_dir: The base directory to resolve relative paths against.
        exclusion_config: Exclusion rules to apply.
        verbose: If True, collect verbose messages about skipped files.

    Returns:
        A tuple of (collected files sorted by path, verbose messages).
    """
    return resolve_paths(topic.paths, base_dir, exclusion_config, verbose)


def _collect_directory(
    dir_path: str,
    base_dir: str,
    exclusion_config: ExclusionConfig,
    files: list[CollectedFile],
    seen: set[str],
    messages: list[str],
    verbose: bool,
) -> None:
    """Recursively collect all files from a directory."""
    for root, dirs, filenames in os.walk(dir_path):
        # Filter out excluded directories in-place to prevent os.walk from descending
        dirs[:] = [
            d for d in dirs
            if d not in exclusion_config.excluded_dirs
        ]
        dirs.sort()

        for filename in sorted(filenames):
            filepath = os.path.join(root, filename)
            _collect_file(filepath, base_dir, exclusion_config, files, seen, messages, verbose)


def _collect_file(
    filepath: str,
    base_dir: str,
    exclusion_config: ExclusionConfig,
    files: list[CollectedFile],
    seen: set[str],
    messages: list[str],
    verbose: bool,
) -> None:
    """Collect a single file if it passes exclusion checks."""
    abs_path = os.path.abspath(filepath)
    if abs_path in seen:
        return
    seen.add(abs_path)

    rel_path = os.path.relpath(abs_path, base_dir)

    reason = is_excluded(abs_path, exclusion_config, base_dir)
    if reason is not None:
        if verbose:
            messages.append(f"  Skipped {rel_path}: {reason}")
        return

    try:
        with open(abs_path, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        messages.append(f"  Warning: cannot read {rel_path}: {e}")
        return

    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    size = os.path.getsize(abs_path)

    files.append(CollectedFile(
        relative_path=rel_path,
        absolute_path=abs_path,
        content=content,
        size=size,
        line_count=line_count,
    ))
