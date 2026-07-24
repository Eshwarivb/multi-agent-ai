from agents.writer import clean_patch_output, code_writer_node


def test_clean_patch_output():
    raw_markdown = "Here is the diff:\n```diff\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new\n```"
    cleaned = clean_patch_output(raw_markdown)
    assert cleaned.startswith("--- a/file.py")
    assert cleaned.endswith("+new")


def test_code_writer_node_execution():
    state = {
        "issue": {"title": "Fix crash", "body": "Division by zero crash"},
        "plan": ["1. Check denominator"],
        "code_context": ["File: math_ops.py\ndef divide(a, b):\n    return a / b"],
        "patch": "",
        "test_results": {},
        "retry_count": 0,
        "pr_url": None,
    }

    result = code_writer_node(state)
    assert "patch" in result
    assert "--- a/math_ops.py" in result["patch"]
    assert "+++ b/math_ops.py" in result["patch"]
