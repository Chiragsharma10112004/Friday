from app.core.planner.planner import decide_tool
from app.core.runtime.manager import execute_tool


def process_tools(message: str, previous_steps: str = ""):
    """
    Execute one tool selected by the planner.
    Returns the execution result and an updated history string.
    """

    plan = decide_tool(
        user_request=message,
        previous_steps=previous_steps
    )

    if not plan.get("use_tool"):
        return None

    tool_name = plan["tool"]
    action = plan["action"]

    kwargs = {
        key: value
        for key, value in plan.items()
        if key not in (
            "use_tool",
            "tool",
            "action",
        )
    }

    result = execute_tool(
        tool_name=tool_name,
        action=action,
        **kwargs
    )

    history = previous_steps

    history += (
        f"\nTool: {tool_name}"
        f"\nAction: {action}"
        f"\nResult: {result}\n"
    )

    return {
        "plan": plan,
        "result": result,
        "history": history,
    }
