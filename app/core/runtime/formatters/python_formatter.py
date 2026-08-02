def format_python(action, result):
    """
    Format the output returned by the Python execution tool.
    """

    if result.get("success"):

        output = result.get("stdout", "").strip()

        if not output:
            output = "(No Output)"

        return (
            "🐍 Python Execution\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ Status : Success\n\n"
            f"{output}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Exit Code : {result.get('returncode', 0)}"
        )

    error = (
        result.get("stderr")
        or result.get("error")
        or "Unknown Error"
    )

    return (
        "🐍 Python Execution\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ Status : Failed\n\n"
        f"{error}"
    )
