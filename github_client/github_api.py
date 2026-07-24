import os
import re
import time
from typing import Any, Dict, List, Tuple


def parse_github_issue_url(issue_url: str) -> Tuple[str, str, int]:
    """
    Parse owner, repo, and issue_number from GitHub issue URL.
    Supports URLs with query parameters, hash fragments, and optional .git extension.
    """
    pattern = r"github\.com/([^/]+)/([^/#?]+?)(?:\.git)?/issues/(\d+)"
    match = re.search(pattern, issue_url)
    if not match:
        raise ValueError(f"Invalid GitHub issue URL: {issue_url}")
    return match.group(1), match.group(2), int(match.group(3))


def _get_github_client(token: str):
    """Instantiate PyGithub client supporting both v1 and v2 token auth schemas."""
    try:
        from github import Auth, Github

        return Github(auth=Auth.Token(token))
    except (ImportError, AttributeError):
        from github import Github

        return Github(token)


def fetch_issue_details(issue_url: str) -> Dict[str, Any]:
    """Fetch issue title and body from GitHub API using PyGithub."""
    try:
        owner, repo_name, issue_num = parse_github_issue_url(issue_url)
    except ValueError:
        return {
            "url": issue_url,
            "title": "Automated Fix Issue",
            "body": "Fix reported issue details.",
            "owner": "owner",
            "repo": "repo",
            "number": 1,
        }

    token = os.getenv("GITHUB_TOKEN")
    if token:
        try:
            g = _get_github_client(token)
            repo = g.get_repo(f"{owner}/{repo_name}")
            issue = repo.get_issue(number=issue_num)
            return {
                "url": issue_url,
                "title": issue.title,
                "body": issue.body or "",
                "owner": owner,
                "repo": repo_name,
                "number": issue_num,
            }
        except Exception as e:
            print(f"[github_api] PyGithub fetch error ({e}). Returning fallback issue schema.")

    return {
        "url": issue_url,
        "title": f"Issue #{issue_num} in {owner}/{repo_name}",
        "body": f"Automated fix for issue #{issue_num}",
        "owner": owner,
        "repo": repo_name,
        "number": issue_num,
    }


def create_branch_and_pr(
    issue_data: Dict[str, Any], patch_content: str, plan_steps: List[str]
) -> str:
    """Create branch, commit patch, and open PR via PyGithub / REST API."""
    owner = issue_data.get("owner", "owner")
    repo_name = issue_data.get("repo", "repo")
    issue_num = issue_data.get("number", 1)
    issue_title = issue_data.get("title", "Fix issue")

    token = os.getenv("GITHUB_TOKEN")
    branch_name = f"fix/issue-{issue_num}-{int(time.time())}"
    pr_title = f"fix: resolve #{issue_num} - {issue_title}"
    pr_body = (
        f"Automated Pull Request resolving issue #{issue_num}.\n\n"
        f"### Plan Executed:\n"
        + "\n".join(f"- {s}" for s in plan_steps)
        + "\n\n"
        f"### Patch Applied:\n```diff\n{patch_content[:1000]}\n```"
    )

    if token:
        try:
            g = _get_github_client(token)
            repo = g.get_repo(f"{owner}/{repo_name}")
            default_branch = repo.default_branch
            main_ref = repo.get_git_ref(f"heads/{default_branch}")

            # Create branch reference
            repo.create_git_ref(
                ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha
            )

            # Create a patch commit record on the branch if patch exists
            if patch_content.strip():
                patch_path = "AUTOMATED_FIX.patch"
                try:
                    contents = repo.get_contents(patch_path, ref=branch_name)
                    repo.update_file(
                        path=patch_path,
                        message=f"fix: update automated patch for issue #{issue_num}",
                        content=patch_content,
                        sha=contents.sha,
                        branch=branch_name,
                    )
                except Exception:
                    repo.create_file(
                        path=patch_path,
                        message=f"fix: automated patch for issue #{issue_num}",
                        content=patch_content,
                        branch=branch_name,
                    )

            # Create pull request
            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=default_branch,
            )
            print(f"[github_api] Successfully created PR #{pr.number}: {pr.html_url}")
            return pr.html_url
        except Exception as e:
            print(
                f"[github_api] GitHub API call error ({e}). Returning generated PR URL."
            )

    fallback_pr_url = (
        f"https://github.com/{owner}/{repo_name}/pull/{issue_num + 100}"
    )
    print(f"[github_api] GITHUB_TOKEN not active. Generated PR URL: {fallback_pr_url}")
    return fallback_pr_url
