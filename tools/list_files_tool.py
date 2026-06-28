from __future__ import annotations

import fnmatch
from pathlib import Path

from langchain_core.tools import StructuredTool

from config import MAX_LIST_RESULTS, relative_to_root, resolve_inside_root, should_ignore


def make_list_files_tool(repo_root: str) -> StructuredTool:
    def list_files(
        directory: str = ".",
        pattern: str = "*",
        max_results: int = MAX_LIST_RESULTS,
    ) -> str:
        """List files and directories inside the repository."""
        try:
            start = resolve_inside_root(repo_root, directory)
        except Exception as exc:
            return f"ERROR: {exc}"

        max_results = max(1, min(max_results, MAX_LIST_RESULTS))
        if start.is_file():
            return relative_to_root(repo_root, start)

        rows: list[str] = []
        truncated = False
        for path in sorted(start.rglob("*")):
            rel_path = Path(relative_to_root(repo_root, path))
            if should_ignore(rel_path):
                continue
            if not fnmatch.fnmatch(path.name, pattern) and not fnmatch.fnmatch(str(rel_path), pattern):
                continue
            marker = "/" if path.is_dir() else ""
            rows.append(f"{rel_path}{marker}")
            if len(rows) >= max_results:
                truncated = True
                break

        if not rows:
            return "No matching files."
        suffix = "\n\n[truncated]" if truncated else ""
        return "\n".join(rows) + suffix

    return StructuredTool.from_function(
        func=list_files,
        name="list_files",
        description=(
            "List repo files or directories. Use this before reading when the user asks "
            "about project structure, a folder, or available files."
        ),
    )
