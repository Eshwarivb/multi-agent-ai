from github_client.github_api import create_branch_and_pr
from graph.state import AgentState


def pr_opener_node(state: AgentState) -> dict:
    print("[pr_opener_node] Pushing branch and opening Pull Request via GitHub API...")
    issue = state.get("issue", {})
    patch = state.get("patch", "")
    plan = state.get("plan", [])

    pr_url = create_branch_and_pr(
        issue_data=issue, patch_content=patch, plan_steps=plan
    )

    return {"pr_url": pr_url}
