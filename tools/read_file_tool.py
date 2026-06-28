from __future__ import annotations

from langchain_core.tools import StructuredTool

from config import (
    MAX_READ_LINES,
    is_probably_text,
    read_text_file,
    relative_to_root,
    resolve_inside_root,
)


def make_read_file_tool(repo_root: str) -> StructuredTool:
    def read_file(path: str, start_line: int = 1, max_lines: int = MAX_READ_LINES) -> str:
        """Read a text/code file with line numbers."""
        try:
            target = resolve_inside_root(repo_root, path)
        except Exception as exc:
            return f"ERROR: {exc}"

        if target.is_dir():
            return f"ERROR: {relative_to_root(repo_root, target)} is a directory. Use list_files first."
        if not is_probably_text(target):
            return f"ERROR: {relative_to_root(repo_root, target)} does not look like a text file."

        start_line = max(1, start_line)
        max_lines = max(1, min(max_lines, MAX_READ_LINES))

        try:
            text, byte_truncated = read_text_file(target)
        except Exception as exc:
            return f"ERROR: failed to read file: {exc}"

        lines = text.splitlines()
        end_line = min(len(lines), start_line + max_lines - 1)
        selected = lines[start_line - 1 : end_line]
        numbered = [f"{idx:>5}: {line}" for idx, line in enumerate(selected, start=start_line)]

        header = f"FILE: {relative_to_root(repo_root, target)} lines {start_line}-{end_line} of {len(lines)}"
        notes = []
        if end_line < len(lines):
            notes.append("line output truncated")
        if byte_truncated:
            notes.append("file bytes truncated")
        footer = f"\n\n[{'; '.join(notes)}]" if notes else ""
        return header + "\n" + "\n".join(numbered) + footer

    return StructuredTool.from_function(
        func=read_file,
        name="read_file",
        description=(
            "Read a repo text/code file by relative path. Use this when answering questions "
            "about concrete file behavior or implementation details."
        ),
    )
