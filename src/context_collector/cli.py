"""Argument parsing, command dispatch, and error handling."""

from __future__ import annotations

import argparse
import os
import sys

from context_collector import __version__
from context_collector.collector import resolve_paths, resolve_topic
from context_collector.config import (
    ConfigError,
    ProjectConfig,
    find_config_file,
    get_repo_name,
    load_config,
)
from context_collector.console import (
    format_size,
    print_dry_run,
    print_error,
    print_size_warning,
    print_success,
    print_topics,
    print_verbose,
)
from context_collector.exclusions import ExclusionConfig
from context_collector.formatter import estimate_output_size, format_output

DEFAULT_SIZE_THRESHOLD = 512_000  # 500 KB


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="context-collector",
        description=(
            "Collect source files from a repository into a single Markdown document, "
            "ready to share with an LLM."
        ),
        epilog=(
            "Examples:\n"
            "  context-collector auth                    Collect the 'auth' topic\n"
            "  context-collector --paths src/api/        Collect all files in src/api/\n"
            "  context-collector auth --dry-run          Preview what would be collected\n"
            "  context-collector --list-topics           List all available topics\n"
            "  context-collector auth -o - | pbcopy      Copy output to clipboard (macOS)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "topic",
        nargs="?",
        default=None,
        metavar="TOPIC",
        help="Topic name from .context-collector.toml",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        metavar="PATH",
        help="Free-form path selection (alternative to TOPIC)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="PATH",
        default=None,
        help="Output file path. Use '-' for stdout. Default: context-<topic>.md or context.md",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="Path to config file (default: .context-collector.toml in cwd or any parent)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without writing output",
    )
    parser.add_argument(
        "--fail-on-large",
        action="store_true",
        help="Exit with error if output exceeds size threshold",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=DEFAULT_SIZE_THRESHOLD,
        metavar="BYTES",
        help=f"Override the size warning threshold (default: {DEFAULT_SIZE_THRESHOLD})",
    )
    parser.add_argument(
        "--no-toc",
        action="store_true",
        help="Skip the table of contents section",
    )
    parser.add_argument(
        "--list-topics",
        action="store_true",
        help="List all defined topics with their descriptions and exit",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed information about what is being collected",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"context-collector {__version__}",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Main entry point for the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    base_dir = os.getcwd()

    # Load config if needed
    config: ProjectConfig | None = None
    if args.config:
        try:
            config = load_config(args.config)
        except ConfigError as e:
            print_error(str(e))
            sys.exit(1)
    elif args.list_topics or (args.topic and not args.paths):
        config_path = find_config_file()
        if config_path:
            try:
                config = load_config(config_path)
            except ConfigError as e:
                print_error(str(e))
                sys.exit(1)

    # Handle --list-topics
    if args.list_topics:
        if config is None:
            print_error(
                "No .context-collector.toml found.\n"
                "Create one in your repository root to define topics.\n"
                "See: https://github.com/t11z/context-collector#configuration"
            )
            sys.exit(1)
        print_topics(config.topics)
        return

    # Validate arguments
    if not args.topic and not args.paths:
        print_error(
            "No topic or paths specified.\n"
            "Usage:\n"
            "  context-collector <topic>           Collect a named topic\n"
            "  context-collector --paths <path>...  Collect specific paths\n"
            "  context-collector --list-topics      List available topics\n\n"
            "Create a .context-collector.toml in your repository root to define topics.\n"
            "See: https://github.com/t11z/context-collector#configuration"
        )
        sys.exit(1)

    if args.topic and args.paths:
        print_error("Cannot specify both a topic and --paths. Use one or the other.")
        sys.exit(1)

    # Resolve files
    exclusion_config = config.exclusion_config if config else ExclusionConfig()

    if args.topic:
        if config is None:
            print_error(
                "No .context-collector.toml found.\n"
                "Create one in your repository root to define topics, "
                "or use --paths for free-form selection.\n"
                "See: https://github.com/t11z/context-collector#configuration"
            )
            sys.exit(1)

        if args.topic not in config.topics:
            available = ", ".join(sorted(config.topics.keys()))
            print_error(
                f"Topic '{args.topic}' not found in config.\n"
                f"Available topics: {available}"
            )
            sys.exit(1)

        topic = config.topics[args.topic]
        files, messages = resolve_topic(topic, base_dir, exclusion_config, verbose=args.verbose)
        topic_name: str | None = args.topic
        topic_description: str | None = topic.description or None
    else:
        assert args.paths is not None
        files, messages = resolve_paths(
            args.paths, base_dir, exclusion_config, verbose=args.verbose
        )
        topic_name = None
        topic_description = None

    if args.verbose and messages:
        print_verbose(messages)

    # Handle empty results
    if not files:
        if not args.quiet:
            print("No files matched the given selection.")
        return

    # Calculate sizes
    total_content_size = sum(f.size for f in files)
    output_estimate = estimate_output_size(files)

    # Dry run
    if args.dry_run:
        print_dry_run(files, output_estimate)
        return

    # Size warning
    if output_estimate > args.max_size:
        if not args.quiet:
            print_size_warning(output_estimate, files, args.max_size)
        if args.fail_on_large:
            print_error(
                f"Output size ({format_size(output_estimate)}) exceeds threshold "
                f"({format_size(args.max_size)}). Use --max-size to adjust."
            )
            sys.exit(1)

    # Generate output
    repo_name = get_repo_name()
    output = format_output(
        files=files,
        repo_name=repo_name,
        topic_name=topic_name,
        topic_description=topic_description,
        include_toc=not args.no_toc,
    )

    # Determine output path
    if args.output == "-":
        sys.stdout.write(output)
        return

    if args.output:
        output_path = args.output
    elif topic_name:
        output_path = f"context-{topic_name}.md"
    else:
        output_path = "context.md"

    # Write output
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
    except OSError as e:
        print_error(f"Cannot write output file: {e}")
        sys.exit(1)

    if not args.quiet:
        print_success(files, total_content_size, output_path, topic_name)
