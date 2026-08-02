from app.core.planner.registry import TOOLS


def execute_tool(tool_name, action, **kwargs):
    """
    Execute a tool action.
    """

    tool = TOOLS.get(tool_name)

    if tool is None:
        return {
            "success": False,
            "error": "Unknown tool."
        }

    func = tool.get(action)

    if func is None:
        return {
            "success": False,
            "error": "Unknown action."
        }

    return func(**kwargs)
