import os
import tempfile
from sandbox.docker_runner import run_tests_in_docker
from agents.tester import test_writer_node


def test_sandbox_isolated_test_runner():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample test file in tmpdir
        test_file = os.path.join(tmpdir, "test_sample.py")
        with open(test_file, "w") as f:
            f.write("def test_dummy():\n    assert 1 + 1 == 2\n")

        # Run with dummy patch
        res = run_tests_in_docker(repo_path=tmpdir, patch_content="")
        assert res["passed"] is True
        assert "1 passed" in res["output"] or "passed" in res["output"].lower()


def test_test_writer_node_empty_patch():
    state = {
        "issue": {"title": "Test Issue", "body": "Body", "repo_path": "."},
        "patch": "",
        "retry_count": 0,
    }
    result = test_writer_node(state)
    assert result["test_results"]["passed"] is False
    assert result["retry_count"] == 1
