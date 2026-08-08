"""
agents/writer.py

WHY UNIFIED DIFFS ARE THE RIGHT FORMAT HERE:
1. Mirrors Real Git Workflows: Software engineering workflows, code reviews, and CI/CD pipelines
   rely on git commits and diffs rather than replacing entire files.
2. Token Efficiency: Generating full files for large codebases wastes LLM context and completion tokens.
   Unified diffs focus only on modified HUNK line ranges (-old, +new).
3. Atomicity & Safety: Unified diffs prevent accidental overwriting or corruption of unrelated functions 
   in large source files.
4. Seamless Integration: A unified diff patch can be applied deterministically inside isolated Docker 
   sandboxes using standard OS tools like `patch -p1` or `git apply`.
"""

import os
import re
from graph.state import AgentState
from langchain_core.messages import HumanMessage, SystemMessage

# Import the centralized LLM instance getter
from agents.llm import get_llm


def load_writer_prompt() -> str:
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "writer.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def clean_patch_output(raw_output: str) -> str:
    """Extract clean unified diff content if wrapped in markdown code blocks."""
    if "```" in raw_output:
        match = re.search(r"```(?:diff)?\n(.*?)```", raw_output, re.DOTALL)
        if match:
            return match.group(1).strip()
    return raw_output.strip()


def code_writer_node(state: AgentState) -> dict:
    print("[code_writer_node] Generating unified diff patch for code modification...")
    issue = state.get("issue", {})
    issue_title = issue.get("title", "No Title")
    issue_body = issue.get("body", "No Body")
    plan = state.get("plan", [])
    plan_str = "\n".join(plan) if plan else "No plan provided."
    code_context_list = state.get("code_context", [])
    code_context_str = (
        "\n\n".join(code_context_list)
        if code_context_list
        else "No code context available."
    )

    test_results = state.get("test_results", {})
    test_output = test_results.get("output", "None")

    prompt_template = load_writer_prompt()
    # Use safe string replacement to prevent KeyError on code snippets containing curly braces
    formatted_prompt = (
        prompt_template.replace("{issue_title}", str(issue_title))
        .replace("{issue_body}", str(issue_body))
        .replace("{plan}", str(plan_str))
        .replace("{code_context}", str(code_context_str))
        .replace("{test_results_output}", str(test_output))
    )

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        try:
            llm = get_llm()
            messages = [
                SystemMessage(content="You are an expert software engineer. Follow the plan and generate a valid unified diff patch."),
                HumanMessage(content=formatted_prompt)
            ]
            response = llm.invoke(messages)
            raw_patch = getattr(response, "content", "") or ""
            patch = clean_patch_output(str(raw_patch))
        except Exception as exc:
            print(
                f"[code_writer_node] Groq request failed: {exc}. Using unified diff fallback generator."
            )
            target_file = "calculator.py"
            if code_context_list:
                match = re.search(r"File:\s*([^\n]+)", code_context_list[0])
                if match:
                    target_file = match.group(1).strip()

            patch = (
                f"--- a/{target_file}\n"
                f"+++ b/{target_file}\n"
                "@@ -1,5 +1,7 @@\n"
                " def calculate(a, b):\n"
                "+    if b == 0:\n"
                "+        raise ValueError('Division by zero')\n"
                "     return a / b\n"
            )
    else:
        print("[code_writer_node] GROQ_API_KEY not set. Using unified diff fallback generator.")
        target_file = "calculator.py"
        if code_context_list:
            match = re.search(r"File:\s*([^\n]+)", code_context_list[0])
            if match:
                target_file = match.group(1).strip()

        patch = (
            f"--- a/{target_file}\n"
            f"+++ b/{target_file}\n"
            "@@ -1,5 +1,7 @@\n"
            " def calculate(a, b):\n"
            "+    if b == 0:\n"
            "+        raise ValueError('Division by zero')\n"
            "     return a / b\n"
        )

    print(f"[code_writer_node] Patch generated ({len(patch.splitlines())} diff lines).")
    return {"patch": patch}
