from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from langchain_core.tools import StructuredTool

from config import relative_to_root, resolve_inside_root


def make_delete_file_tool(repo_root: str) -> StructuredTool:
    def delete_path(path: str, recursive: bool = False) -> str:
        """Move a repo file or directory to .codebase_agent_trash."""
        try:
            target = resolve_inside_root(repo_root, path)
        except Exception as exc:
            return f"ERROR: {exc}"

        rel = Path(relative_to_root(repo_root, target))
        if str(rel) in {"", "."}:
            return "ERROR: refusing to delete the repo root."
        if rel.parts and rel.parts[0] == ".codebase_agent_trash":
            return "ERROR: refusing to delete files from the agent trash."
        if target.is_dir() and not recursive:
            return "ERROR: target is a directory. Set recursive=True only if the user explicitly requested it."

        trash_root = resolve_inside_root(repo_root, ".codebase_agent_trash", must_exist=False)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = trash_root / stamp / rel
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(target), str(destination))
        except Exception as exc:
            return f"ERROR: failed to move to trash: {exc}"

        return f"Moved {rel} to {relative_to_root(repo_root, destination)}"

    return StructuredTool.from_function(
        func=delete_path,
        name="delete_path",
        description=(
            "Delete a repo path by moving it to .codebase_agent_trash. Only call this if the latest "
            "user message explicitly asks to delete a specific path."
        ),
    )
