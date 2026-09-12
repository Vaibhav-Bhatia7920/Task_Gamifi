from datetime import datetime, timezone
from typing import Any, Dict


def get_current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


TOOL_HANDLERS = {
    "get_current_time": get_current_time,
}


def run_tool(name: str, arguments: Dict[str, Any]) -> str:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return f"Unknown tool: {name}"
    return handler(**arguments)
