from __future__ import annotations

from collections import Counter
from pathlib import Path

from langchain_core.tools import StructuredTool

from config import relative_to_root, resolve_inside_root, should_ignore


IMPORTANT_NAMES = {
    "README.md",
    "readme.md",
    "pyproject.toml",
    "setup.py",
    "requirements.txt",
    "environment.yml",
    "package.json",
    "Dockerfile",
    "Makefile",
    "main.py",
    "app.py",
}


def make_analyze_project_tool(repo_root: str) -> StructuredTool:
    def analyze_project(directory: str = ".", max_files: int = 500) -> str:
        """Summarize project tree, file types, and likely entry points."""
        try:
            start = resolve_inside_root(repo_root, directory)
        except Exception as exc:
            return f"ERROR: {exc}"

        max_files = max(1, min(max_files, 2000))
        if start.is_file():
            return f"File: {relative_to_root(repo_root, start)}"

        file_count = 0
        dir_count = 0
        suffixes: Counter[str] = Counter()
        top_level: list[str] = []
        important: list[str] = []
        truncated = False

        for path in sorted(start.rglob("*")):
            rel = Path(relative_to_root(repo_root, path))
            if should_ignore(rel):
                continue
            if path.is_dir():
                dir_count += 1
                if path.parent == start:
                    top_level.append(f"{rel}/")
                continue

            file_count += 1
            suffixes[path.suffix.lower() or "[no extension]"] += 1
            if path.parent == start:
                top_level.append(str(rel))
            if path.name in IMPORTANT_NAMES or path.name.lower().startswith("readme"):
                important.append(str(rel))
            if file_count >= max_files:
                truncated = True
                break

        suffix_text = ", ".join(f"{k}: {v}" for k, v in suffixes.most_common(12)) or "none"
        top_text = "\n".join(top_level[:80]) or "none"
        important_text = "\n".join(important[:80]) or "none"
        note = "\n[truncated]" if truncated else ""

        return (
            f"ROOT: {relative_to_root(repo_root, start) or '.'}\n"
            f"FILES: {file_count}\n"
            f"DIRS: {dir_count}\n"
            f"FILE_TYPES: {suffix_text}\n\n"
            f"TOP_LEVEL:\n{top_text}\n\n"
            f"IMPORTANT_FILES:\n{important_text}"
            f"{note}"
        )

    return StructuredTool.from_function(
        func=analyze_project,
        name="analyze_project",
        description=(
            "Summarize a repo or subdirectory: counts, top-level tree, file types, and likely entry points. "
            "Use for broad project overview questions."
        ),
    )
