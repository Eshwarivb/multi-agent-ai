from agents.pr import pr_opener_node
from github_client.github_api import (
    create_branch_and_pr,
    fetch_issue_details,
    parse_github_issue_url,
)


def test_parse_github_issue_url():
    url = "https://github.com/psf/requests/issues/5000"
    owner, repo, issue_num = parse_github_issue_url(url)
    assert owner == "psf"
    assert repo == "requests"
    assert issue_num == 5000


def test_parse_github_issue_url_with_query_and_hash():
    url = "https://github.com/owner/repo.git/issues/123?tab=readme-ov-file#issuecomment-9"
    owner, repo, issue_num = parse_github_issue_url(url)
    assert owner == "owner"
    assert repo == "repo"
    assert issue_num == 123


def test_fetch_issue_details_fallback():
    url = "https://github.com/scikit-learn/scikit-learn/issues/1234"
    details = fetch_issue_details(url)
    assert details["owner"] == "scikit-learn"
    assert details["repo"] == "scikit-learn"
    assert details["number"] == 1234


def test_pr_opener_node_execution():
    state = {
        "issue": {
            "owner": "example_org",
            "repo": "example_repo",
            "number": 42,
            "title": "Fix division bug",
        },
        "patch": "--- a/file.py\n+++ b/file.py",
        "plan": ["1. Apply fix"],
        "pr_url": None,
    }
    res = pr_opener_node(state)
    assert "pr_url" in res
    assert "github.com/example_org/example_repo/pull/142" in res["pr_url"]
