import argparse
import sys
from dotenv import load_dotenv

load_dotenv()

from graph.workflow import build_graph


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent GitHub Issue-to-PR Orchestration System"
    )
    parser.add_argument(
        "--issue-url",
        type=str,
        required=True,
        help="URL of the GitHub issue to resolve (e.g., https://github.com/owner/repo/issues/123)",
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        default=".",
        help="Local repository path to examine and modify",
    )

    args = parser.parse_args()
    print(f"Orchestration system initialized for issue: {args.issue_url}")
    print(f"Target local repository path: {args.repo_path}")

    # Build and invoke compiled state graph
    app_graph = build_graph()
    initial_state = {
        "issue": {"url": args.issue_url, "title": "Stub Issue", "body": "Stub Body"},
        "code_context": [],
        "plan": [],
        "patch": "",
        "test_results": {"passed": False, "output": ""},
        "retry_count": 0,
        "pr_url": None,
    }

    print("\n--- Starting Agent Graph Execution ---")
    final_state = app_graph.invoke(initial_state)
    print("--- Graph Execution Completed Successfully ---\n")
    print(f"Final PR URL: {final_state.get('pr_url')}")


if __name__ == "__main__":
    main()
