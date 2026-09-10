import logging
import re

logger = logging.getLogger("friday.runtime.python")


def format_python(action, result):
    """
    Format the output returned by the Python execution tool.
    Internal logs retain complete raw stderr/tracebacks.
    User output is formatted cleanly without internal path leakage.
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

    raw_error = (
        result.get("stderr")
        or result.get("error")
        or "Unknown Error"
    )

    # Log full traceback internally
    logger.warning("Python execution failed: %s", raw_error)

    # Sanitize user display: strip internal filesystem paths and extract the core exception line
    cleaned_err = str(raw_error).strip()
    lines = [l.strip() for l in cleaned_err.split("\n") if l.strip()]

    # Extract final exception line if multiline traceback
    if "Traceback (most recent call last)" in cleaned_err:
        last_line = lines[-1] if lines else "RuntimeError"
        user_err = f"Runtime Error: {last_line}"
    else:
        # Strip absolute local paths
        user_err = re.sub(r"[A-Za-z]:\\[^ \n\r\t\"']+", "[path]", cleaned_err)
        user_err = re.sub(r"/(?:Users|home|var|tmp|etc|usr|bin|root)/[^ \n\r\t\"']+", "[path]", user_err)

    return (
        "🐍 Python Execution\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ Status : Failed\n\n"
        f"{user_err}"
    )

