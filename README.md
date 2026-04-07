# llm-context-collector

A small CLI tool to collect source files from a repository into a single Markdown document, ready to share with an LLM.

```
$ llm-context-collector auth
✓ Collected 8 files (47 KB) from topic 'auth'
  Written to: context-auth.md
```

## Why

LLM architecture sparring sessions — whether you're debugging a tricky issue, reviewing an approach, or exploring a refactor — work best when the model can see the full picture. But getting code into a chat interface means copy-pasting files one by one, losing track of what you've shared, and spending more time on context assembly than on the actual conversation.

llm-context-collector automates the boring part. You define topics in a config file (or just point at directories), run one command, and get a single Markdown file with all the relevant source code, properly formatted with syntax highlighting and a table of contents. Drop it into Claude, ChatGPT, Gemini, or any other LLM, and start the conversation with full context.

## Installation

The recommended way to install is with [pipx](https://pypa.github.io/pipx/), which installs the tool in an isolated environment:

```bash
pipx install llm-context-collector
```

Alternatively, install with pip:

```bash
pip install llm-context-collector
```

For local development:

```bash
git clone https://github.com/t11z/context-collector.git
cd context-collector
pip install -e ".[dev]"
```

## Quick Start

1. Create a `.llm-context-collector.toml` in your repository root:

```toml
[topics.auth]
description = "Authentication flow"
paths = [
  "backend/api/auth.py",
  "backend/security/",
  "frontend/src/hooks/useAuth.ts",
]
```

2. Run the tool:

```bash
llm-context-collector auth
```

3. Upload the generated `context-auth.md` to your LLM chat.

That's it. The file contains all the specified source code in a single, well-formatted Markdown document.

## Configuration

llm-context-collector reads its configuration from `.llm-context-collector.toml` in your repository root (or any parent directory). The config file defines **topics** — named collections of files that you frequently share together.

### Topics

Each topic has a name, an optional description, and a list of paths:

```toml
[topics.auth]
description = "Authentication flow: login, JWT, password handling, user registration"
paths = [
  "backend/api/auth.py",
  "backend/security/jwt.py",
  "backend/security/password.py",
  "backend/domain/models.py",
  "frontend/src/pages/Login.tsx",
  "frontend/src/pages/Register.tsx",
  "frontend/src/hooks/useAuth.ts",
  "backend/tests/integration/test_api_auth.py",
]

[topics.scan-pipeline]
description = "Scan worker, hashing, duplicate detection"
paths = [
  "backend/worker/",
  "backend/adapters/hashing/",
  "backend/domain/scanning.py",
  "backend/ports/hasher.py",
]
```

Paths can be:

- **Exact file paths** — `backend/api/auth.py`
- **Directory paths** — `backend/worker/` — all files within are included recursively
- **Glob patterns** — `backend/**/*_repo.py` — standard glob semantics

### Exclusions

By default, llm-context-collector excludes common generated files, binaries, lock files, and any file larger than 1 MB. You can customize this:

```toml
[exclusions]
# Add project-specific exclusions
additional = ["docs/generated/", "*.snapshot.json"]

# Remove default exclusions if you really need to include them
remove_defaults = ["*.svg"]

# Override the maximum file size (in bytes, default: 1048576 = 1 MB)
max_file_size = 2097152
```

**Default exclusions include:**

- Version control directories (`.git/`, `.svn/`, `.hg/`)
- Generated directories (`node_modules/`, `venv/`, `__pycache__/`, `dist/`, `build/`, etc.)
- Compiled artifacts (`*.pyc`, `*.o`, `*.so`, `*.dll`, `*.class`)
- Lock files (`*.lock`, `package-lock.json`, `yarn.lock`, etc.)
- Minified files (`*.min.js`, `*.min.css`, `*.map`)
- Binary and image files (`*.jpg`, `*.png`, `*.pdf`, `*.zip`, etc.)
- Any file not valid UTF-8
- Any file larger than 1 MB

## Usage

```
Usage: llm-context-collector [TOPIC] [OPTIONS]

Arguments:
  TOPIC                   Topic name from .llm-context-collector.toml

Options:
  --paths PATH [PATH ...] Free-form path selection (alternative to TOPIC)
  -o, --output PATH       Output file path. Use '-' for stdout.
                          Default: context-<topic>.md or context.md
  --config PATH           Path to config file
  --dry-run               List files without writing output
  --fail-on-large         Exit with error if output exceeds size threshold
  --max-size BYTES        Override size warning threshold (default: 512000)
  --no-toc                Skip the table of contents section
  --list-topics           List all defined topics and exit
  -q, --quiet             Suppress all output except errors
  -v, --verbose           Print detailed info about collection
  --version               Print version and exit
  -h, --help              Show help and exit
```

### Examples

Collect a named topic:

```bash
llm-context-collector auth
```

Collect specific paths without a config file:

```bash
llm-context-collector --paths backend/api/ backend/security/
```

Preview what would be collected:

```bash
llm-context-collector auth --dry-run
```

List all available topics:

```bash
llm-context-collector --list-topics
```

Write to stdout (for piping to clipboard):

```bash
# macOS
llm-context-collector auth -o - | pbcopy

# Linux
llm-context-collector auth -o - | xclip -selection clipboard
```

Write to a specific file:

```bash
llm-context-collector auth -o ~/Desktop/context.md
```

## Typical Workflows

### Architecture Sparring with Claude

You're about to refactor the authentication system. You want Claude to review the current state and suggest improvements.

```bash
llm-context-collector auth
# Upload context-auth.md to a Claude project or conversation
# "Here's the current auth implementation. I want to add OAuth2 support. What would you change?"
```

### Bug Report with Context

A colleague reports a bug in the scan pipeline. You want to give your LLM the full context to help debug.

```bash
llm-context-collector scan-pipeline
# Upload context-scan-pipeline.md
# "Users report that duplicate detection fails for files > 100MB. Here's the relevant code."
```

### Quick Ad-Hoc Selection

You don't have a topic defined, but you need to share a few specific files:

```bash
llm-context-collector --paths src/api/endpoints.py src/models/ tests/test_api.py
# Upload context.md
```

### CI Integration

Use `--fail-on-large` in CI to catch accidentally bloated context files:

```bash
llm-context-collector auth --fail-on-large --max-size 200000 -q
```

## Output Format

The generated Markdown file includes:

- A header with the topic name and description
- Metadata: timestamp, repository name, file count, total size
- A table of contents linking to each file
- Each file's contents in a syntax-highlighted code fence

Language detection covers 30+ file extensions including Python, JavaScript, TypeScript, Go, Rust, Java, C/C++, and more. Files with unrecognized extensions use plain code fences.

## FAQ

### Why not just copy-paste files manually?

You can, and for one or two files it's fine. But once you're regularly sharing 5-15 files for architecture discussions, the manual process gets tedious. You forget files, you lose track of what you've shared, and you spend time on logistics instead of the conversation. llm-context-collector makes it a one-command operation.

### Why not use a web tool or IDE extension?

Those work too. llm-context-collector is for people who prefer the terminal, want reproducible topic definitions committed to the repo, and want a tool that works the same way across projects and machines.

### Does it support my programming language?

llm-context-collector doesn't analyze code — it collects files. It works with any text file in any language. The syntax highlighting in the output covers 30+ languages, but even unsupported extensions get included with plain code fences.

### Is it safe to upload my code to an LLM?

This is a decision you and your organization need to make. llm-context-collector does not upload anything — it only writes a local file. What you do with that file is up to you. Consider your company's policies on sharing code with third-party services, and be mindful of secrets, credentials, or proprietary algorithms in the files you collect.

### What about token limits?

llm-context-collector reports file sizes in bytes, not tokens. Different LLMs have different context windows and tokenization schemes, so byte-to-token conversion varies. As a rough guide, 1 KB of code is roughly 250-400 tokens. The tool warns you when the output exceeds 500 KB (~125K-200K tokens), which approaches the limits of most current models.

### Can I use glob patterns?

Yes. Both in the config file paths and with `--paths` on the command line. Standard glob syntax: `*` matches anything except `/`, `**` matches any number of directories, `?` matches a single character.

## Contributing

Contributions are welcome. This is a small, focused tool — please keep PRs small and focused too.

```bash
# Setup
git clone https://github.com/t11z/context-collector.git
cd context-collector
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## License

MIT — see [LICENSE](LICENSE) for details.
