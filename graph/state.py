from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    issue: Dict[str, Any]
    code_context: List[str]  # relevant file paths + snippets
    plan: List[str]  # ordered steps
    patch: str  # unified diff format
    test_results: Dict[str, Any]  # {"passed": bool, "output": str}
    retry_count: int
    pr_url: Optional[str]
    research_done: Optional[bool]  # flag to track deep research iteration
