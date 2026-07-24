import json
import os
import re
from typing import List
from pydantic import BaseModel, Field
from graph.state import AgentState


class PlanOutput(BaseModel):
    analysis: str = Field(description="Brief analysis of the issue and root cause.")
    is_complex: bool = Field(
        description="True if changes span multiple files or architectural modifications; False if simple single file change."
    )
    steps: List[str] = Field(
        description="Ordered list of specific implementation steps."
    )


def load_planner_prompt() -> str:
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "planner.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _call_gemini(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError("google-genai package is not installed") from exc

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(temperature=0)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=config,
    )
    return getattr(response, "text", "") or ""


def _extract_json_payload(raw_output: str) -> dict:
    cleaned = raw_output.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1).strip()
    return json.loads(cleaned)


def planner_node(state: AgentState) -> dict:
    print("[planner_node] Generating structured plan using Pydantic schema...")
    issue = state.get("issue", {})
    issue_title = issue.get("title", "No Title")
    issue_body = issue.get("body", "No Body")
    code_context_list = state.get("code_context", [])
    code_context_str = (
        "\n\n".join(code_context_list)
        if code_context_list
        else "No code context available."
    )

    prompt_template = load_planner_prompt()
    # Use safe string replacement to prevent KeyError when code snippets contain curly braces
    formatted_prompt = (
        prompt_template.replace("{issue_title}", str(issue_title))
        .replace("{issue_body}", str(issue_body))
        .replace("{code_context}", str(code_context_str))
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            gemini_prompt = (
                f"{formatted_prompt}\n\n"
                "Return valid JSON only with this structure: "
                '{"analysis": "...", "is_complex": true, "steps": ["..."]}'
            )
            raw_output = _call_gemini(gemini_prompt)
            payload = _extract_json_payload(raw_output)
            plan_output = PlanOutput.model_validate(payload)
        except Exception as exc:
            print(
                f"[planner_node] Gemini request failed: {exc}. Using structured Pydantic fallback mode."
            )
            is_complex = (
                len(code_context_list) > 2
                or "refactor" in str(issue_title).lower()
                or "architecture" in str(issue_body).lower()
            )
            plan_output = PlanOutput(
                analysis=f"Analysis for: {issue_title}",
                is_complex=is_complex,
                steps=[
                    f"1. Examine context files ({len(code_context_list)} files identified).",
                    f"2. Apply fix for issue: '{issue_title}'.",
                    "3. Write pytest unit tests to verify the fix.",
                ],
            )
    else:
        print("[planner_node] GEMINI_API_KEY not set. Using structured Pydantic fallback mode.")
        is_complex = (
            len(code_context_list) > 2
            or "refactor" in str(issue_title).lower()
            or "architecture" in str(issue_body).lower()
        )
        plan_output = PlanOutput(
            analysis=f"Analysis for: {issue_title}",
            is_complex=is_complex,
            steps=[
                f"1. Examine context files ({len(code_context_list)} files identified).",
                f"2. Apply fix for issue: '{issue_title}'.",
                "3. Write pytest unit tests to verify the fix.",
            ],
        )

    print(
        f"[planner_node] Plan generated ({len(plan_output.steps)} steps, is_complex={plan_output.is_complex})."
    )

    issue_data = dict(issue)
    issue_data["is_complex"] = plan_output.is_complex

    return {"plan": plan_output.steps, "issue": issue_data}
