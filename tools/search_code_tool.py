from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from langchain_core.tools import StructuredTool

from config import (
    MAX_SEARCH_RESULTS,
    is_probably_text,
    read_text_file,
    relative_to_root,
    resolve_inside_root,
    should_ignore,
)


def make_search_code_tool(repo_root: str) -> StructuredTool:
    def search_code(
        query: str,
        directory: str = ".",
        file_pattern: str = "*",
        regex: bool = False,
        case_sensitive: bool = False,
        max_results: int = MAX_SEARCH_RESULTS,
    ) -> str:
        """Search code/text files for a string or regular expression."""
        if not query:
            return "ERROR: query is empty."
        try:
            start = resolve_inside_root(repo_root, directory)
        except Exception as exc:
            return f"ERROR: {exc}"

        max_results = max(1, min(max_results, MAX_SEARCH_RESULTS))
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query if regex else re.escape(query), flags)
        except re.error as exc:
            return f"ERROR: invalid regex: {exc}"

        candidates = [start] if start.is_file() else sorted(start.rglob("*"))
        rows: list[str] = []
        scanned = 0
        for path in candidates:
            rel = Path(relative_to_root(repo_root, path))
            if path.is_dir() or should_ignore(rel):
                continue
            if not fnmatch.fnmatch(path.name, file_pattern) and not fnmatch.fnmatch(str(rel), file_pattern):
                continue
            if not is_probably_text(path):
                continue
            scanned += 1
            try:
                text, _ = read_text_file(path)
            except Exception:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    rows.append(f"{rel}:{idx}: {line.strip()[:240]}")
                    if len(rows) >= max_results:
                        return "\n".join(rows) + f"\n\n[truncated after scanning {scanned} files]"

        if not rows:
            return f"No matches after scanning {scanned} files."
        return "\n".join(rows)

    return StructuredTool.from_function(
        func=search_code,
        name="search_code",
        description=(
            "Search repo code/text for symbols, strings, functions, classes, imports, or error messages. "
            "Use this before reading files when the relevant path is unknown."
        ),
    )
