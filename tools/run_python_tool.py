from __future__ import annotations

import os
import shlex
import subprocess
import sys

from langchain_core.tools import StructuredTool

from config import MAX_RUN_OUTPUT_CHARS, MAX_RUN_TIMEOUT, relative_to_root, resolve_inside_root


def make_run_python_tool(repo_root: str) -> StructuredTool:
    def run_python_file(
        script_path: str,
        arguments: str = "",
        working_directory: str = ".",
        timeout_seconds: int = 20,
    ) -> str:
        """Run a Python file inside the repository and return stdout/stderr."""
        try:
            script = resolve_inside_root(repo_root, script_path)
            cwd = resolve_inside_root(repo_root, working_directory)
        except Exception as exc:
            return f"ERROR: {exc}"

        if not script.is_file():
            return f"ERROR: {relative_to_root(repo_root, script)} is not a file."
        if script.suffix != ".py":
            return "ERROR: run_python_file only runs .py files."
        if not cwd.is_dir():
            return f"ERROR: working_directory is not a directory: {working_directory}"

        timeout_seconds = max(1, min(timeout_seconds, MAX_RUN_TIMEOUT))
        try:
            argv = [sys.executable, str(script), *shlex.split(arguments)]
        except ValueError as exc:
            return f"ERROR: invalid arguments: {exc}"

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{env.get('PYTHONPATH', '')}"

        try:
            proc = subprocess.run(
                argv,
                cwd=str(cwd),
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            return (
                f"TIMEOUT after {timeout_seconds}s while running {relative_to_root(repo_root, script)}\n"
                f"STDOUT:\n{stdout[-MAX_RUN_OUTPUT_CHARS:]}\n"
                f"STDERR:\n{stderr[-MAX_RUN_OUTPUT_CHARS:]}"
            )
        except Exception as exc:
            return f"ERROR: failed to run file: {exc}"

        stdout = proc.stdout[-MAX_RUN_OUTPUT_CHARS:]
        stderr = proc.stderr[-MAX_RUN_OUTPUT_CHARS:]
        return (
            f"COMMAND: {' '.join(shlex.quote(x) for x in argv)}\n"
            f"CWD: {relative_to_root(repo_root, cwd) or '.'}\n"
            f"EXIT_CODE: {proc.returncode}\n\n"
            f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}"
        )

    return StructuredTool.from_function(
        func=run_python_file,
        name="run_python_file",
        description=(
            "Run a Python file inside the repo using the current Python interpreter. "
            "Use only when the user asks to run, test, debug, or verify behavior."
        ),
    )
