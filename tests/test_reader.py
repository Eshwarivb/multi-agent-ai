import os
import tempfile
from agents.reader import extract_keywords, scan_repository, code_reader_node


def test_extract_keywords():
    text = "Fix authentication error in login_user function"
    keywords = extract_keywords(text)
    assert "authentication" in keywords
    assert "login_user" in keywords
    assert "function" in keywords
    assert "fix" not in keywords  # stop word


def test_scan_repository_heuristics():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_file = os.path.join(tmpdir, "auth.py")
        with open(sample_file, "w") as f:
            f.write("def login_user(username, password):\n    # TODO: implement authentication\n    pass\n")

        snippets = scan_repository(tmpdir, ["login_user", "authentication"])
        assert len(snippets) == 1
        assert "File: auth.py" in snippets[0]
        assert "def login_user" in snippets[0]


def test_code_reader_node():
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_file = os.path.join(tmpdir, "calculator.py")
        with open(sample_file, "w") as f:
            f.write("def add(a, b):\n    return a + b\n")

        state = {
            "issue": {
                "title": "Bug in add function in calculator",
                "body": "The addition fails for negative numbers",
                "repo_path": tmpdir,
            },
            "code_context": [],
            "plan": [],
            "patch": "",
            "test_results": {},
            "retry_count": 0,
            "pr_url": None,
        }

        result = code_reader_node(state)
        assert len(result["code_context"]) > 0
        assert "calculator.py" in result["code_context"][0]
