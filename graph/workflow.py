from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from graph.nodes import build_tools, make_agent_node, should_continue
from graph.state import AgentState


def build_workflow(repo_path: str):
    tools = build_tools(repo_path)

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", make_agent_node(repo_path, tools))
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()
