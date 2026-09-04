from app.core.planner.planner import decide_tool
from app.core.runtime.manager import execute_tool


def process_tools(message: str, previous_steps: str = ""):
    """
    Execute one tool selected by the planner.
    Returns the execution result and an updated history string.
    """
    try:
        plan = decide_tool(
            user_request=message,
            previous_steps=previous_steps
        )
    except Exception:
        return None

    if not plan or not isinstance(plan, dict) or not plan.get("use_tool"):
        return None

    tool_name = plan.get("tool")
    action = plan.get("action")

    if not tool_name or not action:
        return None

    kwargs = {
        key: value
        for key, value in plan.items()
        if key not in (
            "use_tool",
            "tool",
            "action",
        )
    }

    try:
        result = execute_tool(
            tool_name=tool_name,
            action=action,
            **kwargs
        )
    except Exception as err:
        result = f"Tool execution failed: {str(err)}"

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
