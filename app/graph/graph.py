"""LangGraph Stateful Workflow Builder with Human-in-the-Loop Approval."""
import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import SalesState
from app.graph.nodes.research import research_node
from app.graph.nodes.prioritize import prioritize_node
from app.graph.nodes.strategy import strategy_node
from app.graph.nodes.communication import communication_node
from app.graph.nodes.approval import approval_node
from app.graph.nodes.action import action_node
from app.graph.nodes.verification import verification_node

logger = logging.getLogger("gwc.graph")


def approval_router(state: SalesState) -> str:
    """Route based on human approval status."""
    status = state.get("approval_status")
    if status in ["APPROVED", "MODIFIED"]:
        return "action"
    return END


def create_sales_graph(checkpointer: MemorySaver = None):
    """Builds and compiles the end-to-end sales intelligence LangGraph."""
    workflow = StateGraph(SalesState)

    # 1. Register all specialized nodes
    workflow.add_node("research", research_node)
    workflow.add_node("prioritize", prioritize_node)
    workflow.add_node("strategy", strategy_node)
    workflow.add_node("communication", communication_node)
    workflow.add_node("approval", approval_node)
    workflow.add_node("action", action_node)
    workflow.add_node("verification", verification_node)

    # 2. Add linear and conditional edges
    workflow.add_edge(START, "research")
    workflow.add_edge("research", "prioritize")
    workflow.add_edge("prioritize", "strategy")
    workflow.add_edge("strategy", "communication")
    workflow.add_edge("communication", "approval")

    # 3. Human Approval conditional branch
    workflow.add_conditional_edges(
        "approval",
        approval_router,
        {
            "action": "action",
            END: END
        }
    )

    workflow.add_edge("action", "verification")
    workflow.add_edge("verification", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    app_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["approval"]
    )
    
    return app_graph


# Global compiled workflow instance
memory_checkpointer = MemorySaver()
sales_graph = create_sales_graph(memory_checkpointer)
