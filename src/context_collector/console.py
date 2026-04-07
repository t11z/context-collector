"""Stderr progress and warning messages."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from context_collector.collector import CollectedFile


def _is_tty() -> bool:
    """Check if stderr is a terminal."""
    return hasattr(sys.stderr, "isatty") and sys.stderr.isatty()


def _bold(text: str) -> str:
    if _is_tty():
        return f"\033[1m{text}\033[0m"
    return text


def _yellow(text: str) -> str:
    if _is_tty():
        return f"\033[33m{text}\033[0m"
    return text


def _green(text: str) -> str:
    if _is_tty():
        return f"\033[32m{text}\033[0m"
    return text


def format_size(size_bytes: int) -> str:
    """Format a byte count as a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def print_success(
    files: list[CollectedFile],
    total_size: int,
    output_path: str,
    topic_name: str | None = None,
) -> None:
    """Print the success message to stdout."""
    count = len(files)
    size_str = format_size(total_size)
    if topic_name:
        print(f"\u2713 Collected {count} files ({size_str}) from topic '{topic_name}'")
    else:
        print(f"\u2713 Collected {count} files ({size_str})")
    print(f"  Written to: {output_path}")


def print_dry_run(files: list[CollectedFile], output_estimate: int) -> None:
    """Print dry-run output to stdout."""
    total_size = sum(f.size for f in files)
    print(f"Would include {len(files)} files ({format_size(total_size)}):")
    for f in files:
        print(f"  {f.relative_path} ({format_size(f.size)}, {f.line_count} lines)")
    print()
    print(f"Total: {len(files)} files, {format_size(total_size)}")
    print(f"Estimated output file size: {format_size(output_estimate)} (including metadata)")


def print_size_warning(
    total_size: int,
    files: list[CollectedFile],
    threshold: int,
) -> None:
    """Print a warning to stderr if output exceeds the size threshold."""
    size_str = format_size(total_size)
    print(
        _yellow(f"\u26a0 Warning: output is {size_str}. This may exceed LLM context limits."),
        file=sys.stderr,
    )
    print("  Consider narrowing the selection. Largest files:", file=sys.stderr)
    sorted_files = sorted(files, key=lambda f: f.size, reverse=True)
    for f in sorted_files[:5]:
        print(f"    {f.relative_path} ({format_size(f.size)})", file=sys.stderr)
    print("  Use --dry-run to see the full breakdown without writing.", file=sys.stderr)


def print_topics(topics: Mapping[str, object]) -> None:
    """Print available topics and their descriptions.

    Args:
        topics: Dict mapping topic name to TopicConfig objects with .description and .paths attrs.
    """
    if not topics:
        print("No topics defined in config file.")
        return

    print("Available topics:")
    for name in sorted(topics):
        topic = topics[name]
        desc = getattr(topic, "description", "")
        path_count = len(getattr(topic, "paths", []))
        if desc:
            print(f"  {_bold(name)} — {desc} ({path_count} path patterns)")
        else:
            print(f"  {_bold(name)} ({path_count} path patterns)")


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def print_verbose(messages: list[str]) -> None:
    """Print verbose messages to stderr."""
    for msg in messages:
        print(msg, file=sys.stderr)
