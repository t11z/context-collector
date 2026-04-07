"""Mapping of file extensions to syntax-highlighting language identifiers."""

# Extension (without dot) → code fence language tag
EXTENSION_MAP: dict[str, str] = {
    "py": "python",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "ts": "typescript",
    "tsx": "tsx",
    "jsx": "jsx",
    "go": "go",
    "rs": "rust",
    "rb": "ruby",
    "java": "java",
    "kt": "kotlin",
    "swift": "swift",
    "c": "c",
    "h": "c",
    "cpp": "cpp",
    "hpp": "cpp",
    "cc": "cpp",
    "hh": "cpp",
    "cs": "csharp",
    "php": "php",
    "sh": "bash",
    "bash": "bash",
    "yml": "yaml",
    "yaml": "yaml",
    "toml": "toml",
    "json": "json",
    "xml": "xml",
    "html": "html",
    "css": "css",
    "scss": "scss",
    "sass": "scss",
    "sql": "sql",
    "md": "markdown",
    "tf": "terraform",
    "bicep": "bicep",
    "dockerfile": "dockerfile",
}

# Files without extensions that have known languages
FILENAME_MAP: dict[str, str] = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "Jenkinsfile": "groovy",
}


def detect_language(filename: str) -> str:
    """Return the code fence language tag for a filename.

    Checks the filename map first (for files like Dockerfile with no extension),
    then falls back to the extension map. Returns an empty string if unknown.
    """
    if filename in FILENAME_MAP:
        return FILENAME_MAP[filename]

    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    return EXTENSION_MAP.get(ext, "")
