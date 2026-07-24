from graph.state import AgentState
from sandbox.docker_runner import run_tests_in_docker


def test_writer_node(state: AgentState) -> dict:
    print("[test_writer_node] Executing tests inside sandboxed container...")
    issue = state.get("issue", {})
    repo_path = issue.get("repo_path") or state.get("repo_path") or "."
    patch = state.get("patch", "")
    current_retry = state.get("retry_count", 0)

    if not patch.strip():
        print("[test_writer_node] Empty patch provided.")
        test_results = {"passed": False, "output": "No patch to execute."}
        return {"test_results": test_results, "retry_count": current_retry + 1}

    results = run_tests_in_docker(repo_path=repo_path, patch_content=patch)

    new_retry = current_retry if results["passed"] else current_retry + 1
    print(
        f"[test_writer_node] Test execution complete. Passed={results['passed']}, RetryCount={new_retry}"
    )

    return {"test_results": results, "retry_count": new_retry}


# Prevent pytest from collecting test_writer_node as a test function fixture
test_writer_node.__test__ = False
