from __future__ import annotations

import os
from pathlib import Path


OLLAMA_MODEL = os.getenv("CODEBASE_AGENT_MODEL", "qwen3:latest")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
TEMPERATURE = float(os.getenv("CODEBASE_AGENT_TEMPERATURE", "0"))
OLLAMA_NUM_CTX = int(os.getenv("CODEBASE_AGENT_NUM_CTX", "8192"))
OLLAMA_NUM_PREDICT = int(os.getenv("CODEBASE_AGENT_NUM_PREDICT", "1024"))
OLLAMA_TIMEOUT = float(os.getenv("CODEBASE_AGENT_OLLAMA_TIMEOUT", "60"))
OLLAMA_REASONING = os.getenv("CODEBASE_AGENT_REASONING", "false").lower() in {"1", "true", "yes", "on"}

MAX_LIST_RESULTS = int(os.getenv("CODEBASE_AGENT_MAX_LIST_RESULTS", "300"))
MAX_SEARCH_RESULTS = int(os.getenv("CODEBASE_AGENT_MAX_SEARCH_RESULTS", "80"))
MAX_READ_LINES = int(os.getenv("CODEBASE_AGENT_MAX_READ_LINES", "240"))
MAX_READ_BYTES = int(os.getenv("CODEBASE_AGENT_MAX_READ_BYTES", str(256 * 1024)))
MAX_RUN_OUTPUT_CHARS = int(os.getenv("CODEBASE_AGENT_MAX_RUN_OUTPUT_CHARS", "12000"))
MAX_RUN_TIMEOUT = int(os.getenv("CODEBASE_AGENT_MAX_RUN_TIMEOUT", "60"))

IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "target",
    ".codebase_agent_trash",
}

TEXT_EXTENSIONS = {
    ".py",
    ".pyi",
    ".txt",
    ".md",
    ".rst",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".tsv",
    ".sh",
    ".bash",
    ".zsh",
    ".c",
    ".h",
    ".cc",
    ".cpp",
    ".cxx",
    ".hpp",
    ".cu",
    ".cuh",
    ".java",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".go",
    ".rs",
    ".r",
    ".m",
    ".swift",
    ".kt",
    ".dockerfile",
}


def normalize_repo_path(repo_path: str | os.PathLike[str]) -> Path:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repo path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repo path is not a directory: {root}")
    return root


def resolve_inside_root(
    repo_root: str | os.PathLike[str],
    user_path: str | os.PathLike[str] = ".",
    *,
    must_exist: bool = True,
) -> Path:
    root = normalize_repo_path(repo_root)
    raw = Path(user_path).expanduser()
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path is outside repo root: {candidate}") from exc

    if must_exist and not candidate.exists():
        raise FileNotFoundError(f"Path does not exist: {candidate}")
    return candidate


def relative_to_root(repo_root: str | os.PathLike[str], path: str | os.PathLike[str]) -> str:
    root = normalize_repo_path(repo_root)
    return str(Path(path).resolve().relative_to(root))


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def is_probably_text(path: Path) -> bool:
    if path.name.lower() in {"dockerfile", "makefile"}:
        return True
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    try:
        with path.open("rb") as fh:
            chunk = fh.read(2048)
    except OSError:
        return False
    return b"\x00" not in chunk


def read_text_file(path: Path, max_bytes: int = MAX_READ_BYTES) -> tuple[str, bool]:
    data = path.read_bytes()
    truncated = len(data) > max_bytes
    if truncated:
        data = data[:max_bytes]
    text = data.decode("utf-8", errors="replace")
    return text, truncated
