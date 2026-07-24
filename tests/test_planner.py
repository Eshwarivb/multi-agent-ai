from agents.planner import PlanOutput, planner_node


def test_plan_output_pydantic_schema():
    plan = PlanOutput(
        analysis="Root cause is missing null check",
        is_complex=False,
        steps=["1. Add null check", "2. Add pytest test"],
    )
    assert plan.is_complex is False
    assert len(plan.steps) == 2


def test_planner_node_fallback():
    state = {
        "issue": {
            "title": "Fix division by zero error in calculator",
            "body": "When denominator is zero, crash occurs",
            "repo_path": ".",
        },
        "code_context": ["File: calculator.py\ndef divide(a, b):\n    return a / b"],
        "plan": [],
        "patch": "",
        "test_results": {},
        "retry_count": 0,
        "pr_url": None,
    }

    result = planner_node(state)
    assert "plan" in result
    assert len(result["plan"]) > 0
    assert result["issue"]["is_complex"] is False


def test_planner_node_with_curly_braces_in_context():
    state = {
        "issue": {
            "title": "Fix dictionary parsing",
            "body": "Dictionary format error",
            "repo_path": ".",
        },
        "code_context": ["File: json_parser.py\ndef parse():\n    return {'key': 'val'}"],
        "plan": [],
        "patch": "",
        "test_results": {},
        "retry_count": 0,
        "pr_url": None,
    }

    result = planner_node(state)
    assert "plan" in result
