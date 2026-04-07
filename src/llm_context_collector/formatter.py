"""Markdown output generation."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from llm_context_collector.console import format_size
from llm_context_collector.languages import detect_language

if TYPE_CHECKING:
    from llm_context_collector.collector import CollectedFile


def _make_anchor(path: str) -> str:
    """Convert a file path to a Markdown-compatible anchor link.

    GitHub-style: lowercase, replace non-alphanumeric with hyphens, strip leading/trailing hyphens.
    """
    anchor = path.lower()
    anchor = re.sub(r"[^a-z0-9\s-]", "", anchor)
    anchor = re.sub(r"[\s]+", "-", anchor)
    anchor = anchor.strip("-")
    return anchor


def format_output(
    files: list[CollectedFile],
    repo_name: str,
    topic_name: str | None = None,
    topic_description: str | None = None,
    include_toc: bool = True,
) -> str:
    """Generate the full Markdown output document.

    Args:
        files: List of collected files to include.
        repo_name: Name of the repository.
        topic_name: Optional topic name for the header.
        topic_description: Optional topic description.
        include_toc: Whether to include the table of contents.

    Returns:
        The complete Markdown document as a string.
    """
    parts: list[str] = []

    # Header
    if topic_name:
        parts.append(f"# Context: {topic_name}\n")
    else:
        parts.append("# Context: Custom Selection\n")

    if topic_description:
        parts.append(f"\n{topic_description}\n")

    # Metadata
    total_size = sum(f.size for f in files)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    parts.append(f"\n**Collected:** {timestamp}  ")
    parts.append(f"\n**Repository:** {repo_name}  ")
    parts.append(f"\n**Files:** {len(files)}  ")
    parts.append(f"\n**Total size:** {format_size(total_size)}\n")

    # Table of contents
    if include_toc and files:
        parts.append("\n## Table of Contents\n\n")
        for f in files:
            anchor = _make_anchor(f.relative_path)
            parts.append(f"- [{f.relative_path}](#{anchor}) — {f.line_count} lines\n")

    # File contents
    for f in files:
        parts.append(f"\n---\n\n## {f.relative_path}\n\n")
        lang = detect_language(f.relative_path.split("/")[-1])
        parts.append(f"```{lang}\n")
        content = f.content
        if content and not content.endswith("\n"):
            content += "\n"
        parts.append(content)
        parts.append("```\n")

    return "".join(parts)


def estimate_output_size(files: list[CollectedFile]) -> int:
    """Estimate the size of the output file including metadata overhead.

    A rough estimate: file contents + ~200 bytes overhead per file for headers and fences.
    """
    content_size = sum(f.size for f in files)
    overhead = len(files) * 200 + 500  # 200 per file header, 500 for document header
    return content_size + overhead
