from langgraph.graph import END, START, StateGraph

from agents.planner import planner_node
from agents.pr import pr_opener_node
from agents.reader import code_reader_node
from agents.tester import test_writer_node
from agents.writer import code_writer_node
from graph.state import AgentState


def route_after_planner(state: AgentState) -> str:
    """
    Routing logic after planner:
    - If plan is complex (multiple files/architecture) and research hasn't been done yet: route to research (code_reader).
    - If plan is simple (single file, <20 lines) or research has completed: route to code_writer.
    """
    issue = state.get("issue", {})
    is_complex = issue.get("is_complex", False)
    research_done = state.get("research_done", False)

    if is_complex and not research_done:
        print("[routing] Complex issue detected. Routing to research step to expand code context...")
        return "code_reader"

    print("[routing] Simple issue or research complete. Routing to code_writer...")
    return "code_writer"


def route_after_test_writer(state: AgentState) -> str:
    """
    Routing logic after test_writer:
    - If tests pass: route to pr_opener.
    - If tests fail and retry_count < 3: route back to code_writer with failure output.
    - If retry_count reaches 3: stop workflow (END).
    """
    test_results = state.get("test_results", {})
    passed = test_results.get("passed", False)
    retry_count = state.get("retry_count", 0)

    if passed:
        print("[routing] Tests passed cleanly. Routing to pr_opener...")
        return "pr_opener"

    if retry_count < 3:
        print(
            f"[routing] Tests failed (retry {retry_count}/3). Routing back to code_writer for patch correction..."
        )
        return "code_writer"

    print(
        f"[routing] Maximum retry limit reached ({retry_count}/3). Terminating graph execution."
    )
    return END


def build_graph():
    builder = StateGraph(AgentState)

    # 1. Register agent nodes
    builder.add_node("code_reader", code_reader_node)
    builder.add_node("planner", planner_node)
    builder.add_node("code_writer", code_writer_node)
    builder.add_node("test_writer", test_writer_node)
    builder.add_node("pr_opener", pr_opener_node)

    # 2. Add entry point edge
    builder.add_edge(START, "code_reader")
    builder.add_edge("code_reader", "planner")

    # 3. Add conditional routing edge after planner
    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {"code_reader": "code_reader", "code_writer": "code_writer"},
    )

    # 4. Standard edge from code_writer to test_writer
    builder.add_edge("code_writer", "test_writer")

    # 5. Add conditional routing edge after test_writer (retry loop or completion)
    builder.add_conditional_edges(
        "test_writer",
        route_after_test_writer,
        {"code_writer": "code_writer", "pr_opener": "pr_opener", END: END},
    )

    # 6. Add terminal edge from pr_opener to END
    builder.add_edge("pr_opener", END)

    return builder.compile()
