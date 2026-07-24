import os
import re
from typing import List, Tuple
from graph.state import AgentState

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now",
    "fix", "bug", "issue", "error", "fail", "failed", "failing", "need", "please", "help"
}

IGNORE_DIRS = {
    ".git", "__pycache__", ".venv", "venv", "env", "node_modules",
    ".pytest_cache", ".mypy_cache", ".idea", ".vscode", "dist", "build"
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe", ".bin", ".png", ".jpg", ".jpeg",
    ".gif", ".zip", ".tar", ".gz", ".7z", ".pdf", ".db", ".sqlite"
}


def extract_keywords(text: str) -> List[str]:
    """Extract meaningful terms from issue title and body."""
    words = re.findall(r'[a-zA-Z_]\w*', text)
    keywords = []
    for w in words:
        w_lower = w.lower()
        if len(w) > 2 and w_lower not in STOP_WORDS:
            keywords.append(w)
            sub_words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\b)|[0-9]+', w)
            for sw in sub_words:
                sw_lower = sw.lower()
                if len(sw) > 2 and sw_lower not in STOP_WORDS and sw_lower not in keywords:
                    keywords.append(sw_lower)
    return list(dict.fromkeys(keywords))


def scan_repository(repo_path: str, keywords: List[str]) -> List[str]:
    """Scan local repository files using heuristic keyword matching against paths and content."""
    if not os.path.exists(repo_path):
        return []

    matched_snippets: List[Tuple[int, str]] = []
    kw_patterns = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords if len(kw) >= 3]

    if not kw_patterns:
        return []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IGNORE_EXTENSIONS:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)

            score = 0
            path_matches = sum(1 for p in kw_patterns if p.search(rel_path))
            score += path_matches * 10

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            matching_line_indices = []
            for idx, line in enumerate(lines):
                line_matches = sum(1 for p in kw_patterns if p.search(line))
                if line_matches > 0:
                    score += line_matches
                    matching_line_indices.append(idx)

            if score > 0 and lines:
                snippet_lines = set()
                for idx in matching_line_indices:
                    start = max(0, idx - 4)
                    end = min(len(lines), idx + 5)
                    for l in range(start, end):
                        snippet_lines.add(l)

                sorted_indices = sorted(snippet_lines)
                if len(sorted_indices) > 50:
                    sorted_indices = sorted_indices[:50]

                snippet_text = "".join(lines[i] for i in sorted_indices)
                formatted = f"File: {rel_path}\n```\n{snippet_text.strip()}\n```"
                matched_snippets.append((score, formatted))

    matched_snippets.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in matched_snippets[:5]]


def code_reader_node(state: AgentState) -> dict:
    print("[code_reader_node] Performing heuristic search for issue context...")
    issue = state.get("issue", {})
    issue_title = issue.get("title", "")
    issue_body = issue.get("body", "")
    full_issue_text = f"{issue_title}\n{issue_body}"

    repo_path = issue.get("repo_path") or state.get("repo_path") or "."

    keywords = extract_keywords(full_issue_text)
    print(f"[code_reader_node] Extracted keywords: {keywords[:10]}")

    context_snippets = scan_repository(repo_path, keywords)
    print(f"[code_reader_node] Found {len(context_snippets)} relevant code snippets.")

    return {"code_context": context_snippets, "research_done": True}
