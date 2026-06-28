from __future__ import annotations

import argparse
import re
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from config import normalize_repo_path
from graph.workflow import build_workflow
from memory.sqlite_memory import SQLiteMemory


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MEMORY_DB = PROJECT_DIR / "memory" / "agent_memory.sqlite3"


def strip_thinking(text: str) -> str:
    return re.sub(r"(?is)<think>.*?</think>\s*", "", text).strip()


def last_ai_text(messages) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content
            if isinstance(content, str):
                return strip_thinking(content)
            return strip_thinking(str(content))
    return ""


def ask_agent(app, repo_path: str, question: str, history, recursion_limit: int) -> str:
    state = {
        "repo_path": repo_path,
        "messages": [*history, HumanMessage(content=question)],
    }
    result = app.invoke(state, config={"recursion_limit": recursion_limit})
    answer = last_ai_text(result["messages"])
    return answer or "(模型没有返回文本答案)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local codebase agent powered by Ollama + LangGraph.")
    parser.add_argument("--repo", default=".", help="Local code repository path to inspect.")
    parser.add_argument("--session-id", default="default", help="SQLite memory session id.")
    parser.add_argument("--memory-db", default=str(DEFAULT_MEMORY_DB), help="SQLite memory database path.")
    parser.add_argument("--no-memory", action="store_true", help="Disable loading/saving conversation memory.")
    parser.add_argument("--clear-memory", action="store_true", help="Clear this session before starting.")
    parser.add_argument("--once", help="Ask one question and exit.")
    parser.add_argument("--recursion-limit", type=int, default=12, help="Max LangGraph steps per question.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo_path = str(normalize_repo_path(args.repo))
    app = build_workflow(repo_path)

    memory = None if args.no_memory else SQLiteMemory(args.memory_db)
    if memory and args.clear_memory:
        memory.clear(args.session_id)

    print(f"Repo: {repo_path}")
    print("输入问题开始对话；输入 /exit 退出，/clear 清空当前会话记忆。")

    def handle(question: str) -> None:
        history = [] if memory is None else memory.load(args.session_id)
        try:
            answer = ask_agent(app, repo_path, question, history, args.recursion_limit)
        except Exception as exc:
            answer = f"ERROR: {type(exc).__name__}: {exc}"
        print(f"\n{answer}\n")
        if memory is not None and not answer.startswith("ERROR:"):
            memory.append(args.session_id, "human", question)
            memory.append(args.session_id, "ai", answer)

    if args.once:
        handle(args.once)
        return

    while True:
        try:
            question = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not question:
            continue
        if question in {"/exit", "exit", "quit", "q"}:
            break
        if question == "/clear":
            if memory is not None:
                memory.clear(args.session_id)
                print("Memory cleared.")
            else:
                print("Memory is disabled.")
            continue
        handle(question)


if __name__ == "__main__":
    main()
