from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.concept_graph import ConceptGraph
from src.agents.graph_state import TutorGraphState
from src.agents.graph_nodes import build_nodes, route_after_update


def build_tutor_graph(cg: ConceptGraph, checkpointer=None):
    """checkpointer defaults to an in-memory one (fine for scripts/tests).
    The API server passes in a persistent SqliteSaver instead."""
    nodes = build_nodes(cg)
    graph_builder = StateGraph(TutorGraphState)

    for name, fn in nodes.items():
        graph_builder.add_node(name, fn)

    graph_builder.add_edge(START, "assess")
    graph_builder.add_edge("assess", "difficulty")
    graph_builder.add_edge("difficulty", "tutor")
    graph_builder.add_edge("tutor", "quiz")
    graph_builder.add_edge("quiz", "collect_answers")
    graph_builder.add_edge("collect_answers", "evaluate")
    graph_builder.add_edge("evaluate", "update")
    graph_builder.add_conditional_edges("update", route_after_update, {"continue": "difficulty", "done": END})

    return graph_builder.compile(checkpointer=checkpointer or MemorySaver())