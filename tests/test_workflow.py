from langgraph.graph import END
from graph.workflow import route_after_planner, route_after_test_writer


def test_route_after_planner_simple():
    state = {
        "issue": {"is_complex": False},
        "research_done": False,
    }
    assert route_after_planner(state) == "code_writer"


def test_route_after_planner_complex():
    state = {
        "issue": {"is_complex": True},
        "research_done": False,
    }
    assert route_after_planner(state) == "code_reader"


def test_route_after_planner_complex_research_done():
    state = {
        "issue": {"is_complex": True},
        "research_done": True,
    }
    assert route_after_planner(state) == "code_writer"


def test_route_after_test_writer_passed():
    state = {
        "test_results": {"passed": True, "output": "OK"},
        "retry_count": 0,
    }
    assert route_after_test_writer(state) == "pr_opener"


def test_route_after_test_writer_failed_retry():
    state = {
        "test_results": {"passed": False, "output": "FAIL"},
        "retry_count": 1,
    }
    assert route_after_test_writer(state) == "code_writer"


def test_route_after_test_writer_max_retries():
    state = {
        "test_results": {"passed": False, "output": "FAIL"},
        "retry_count": 3,
    }
    assert route_after_test_writer(state) == END
