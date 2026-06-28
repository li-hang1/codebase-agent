from __future__ import annotations

from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama

from config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT,
    OLLAMA_REASONING,
    OLLAMA_TIMEOUT,
    TEMPERATURE,
)
from prompts.answer_prompt import ANSWER_PROMPT
from prompts.router_prompt import ROUTER_PROMPT
from tools.analyze_project_tool import make_analyze_project_tool
from tools.delete_file_tool import make_delete_file_tool
from tools.list_files_tool import make_list_files_tool
from tools.read_file_tool import make_read_file_tool
from tools.run_python_tool import make_run_python_tool
from tools.search_code_tool import make_search_code_tool


def build_tools(repo_path: str):
    return [
        make_list_files_tool(repo_path),
        make_read_file_tool(repo_path),
        make_search_code_tool(repo_path),
        make_run_python_tool(repo_path),
        make_delete_file_tool(repo_path),
        make_analyze_project_tool(repo_path),
    ]


def build_llm():
    kwargs = {
        "model": OLLAMA_MODEL,
        "base_url": OLLAMA_BASE_URL,
        "temperature": TEMPERATURE,
        "num_predict": OLLAMA_NUM_PREDICT,
        "reasoning": OLLAMA_REASONING,
        "sync_client_kwargs": {"timeout": OLLAMA_TIMEOUT},
    }
    if OLLAMA_NUM_CTX:
        kwargs["num_ctx"] = OLLAMA_NUM_CTX
    return ChatOllama(**kwargs)


def make_agent_node(repo_path: str, tools):
    llm = build_llm().bind_tools(tools)
    system_prompt = ROUTER_PROMPT.format(repo_path=repo_path) + "\n\n" + ANSWER_PROMPT

    def agent_node(state):
        response = llm.invoke([SystemMessage(content=system_prompt), *state["messages"]])
        return {"messages": [response]}

    return agent_node


def should_continue(state) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "end"
