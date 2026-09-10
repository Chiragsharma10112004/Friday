import logging
import re
from app.core.runtime.formatters.python_formatter import format_python
from app.core.runtime.formatters.filesystem_formatter import format_filesystem
from app.core.runtime.formatters.project_search_formatter import format_project_search
from app.core.runtime.formatters.code_intelligence_formatter import (
    format_code_intelligence,
)

logger = logging.getLogger("friday.runtime")


def sanitize_user_error(raw_error: str, tool_context: str = "Command") -> str:
    """
    Sanitize technical errors, stderr, tracebacks, and missing binaries into safe,
    human-understandable guidance without leaking raw internal paths or shell failures.
    Full technical details remain logged internally for development/debugging.
    """
    if not raw_error:
        return f"{tool_context} could not be completed."

    # Internal technical log
    logger.warning("Tool execution failure [%s]: %s", tool_context, raw_error)

    err_lower = raw_error.lower()

    if "not found" in err_lower or "is not recognized" in err_lower or "no such file or directory" in err_lower:
        match = re.search(r"([a-zA-Z0-9_\-\.]+):\s*(?:not found|is not recognized)", raw_error)
        cmd_name = match.group(1) if match else None
        if cmd_name:
            return f"I can't run that workflow because the required tool or test runner '{cmd_name}' is not configured."
        return "I can't run that workflow because the required tool or test runner is not configured on this host."

    if "permission denied" in err_lower or "access is denied" in err_lower:
        return "The operation was blocked due to local system permission constraints."

    if "timed out" in err_lower or "timeout" in err_lower:
        return "The operation timed out before completing."

    if "connection refused" in err_lower or "failed to establish a new connection" in err_lower:
        return "Could not connect to the required local service or provider endpoint."

    if "syntaxerror" in err_lower:
        return "Execution stopped due to a syntax issue in the code."

    # Strip absolute filesystem paths to protect internal structure
    cleaned = re.sub(r"[A-Za-z]:\\[^ \n\r\t\"']+", "[path]", raw_error)
    cleaned = re.sub(r"/(?:Users|home|var|tmp|etc|usr|bin|root)/[^ \n\r\t\"']+", "[path]", cleaned)

    if "traceback (most recent call last)" in err_lower:
        lines = [l.strip() for l in raw_error.strip().split("\n") if l.strip()]
        last_line = lines[-1] if lines else "Execution failure"
        return f"Execution encountered an error: {last_line}"

    first_line = cleaned.strip().split("\n")[0]
    if len(first_line) > 120:
        first_line = first_line[:117] + "..."
    return f"{tool_context} failed: {first_line}"


def format_terminal(action, result):
    if isinstance(result, dict):
        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            return stdout if stdout else "Command executed successfully with no output."
        raw_error = result.get("stderr") or result.get("error") or "Command execution failed."
        clean_msg = sanitize_user_error(str(raw_error), tool_context="Command")
        return f"❌ {clean_msg}"
    return str(result)


def format_git(action, result):
    if isinstance(result, dict):
        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            return stdout if stdout else "Git operation completed successfully."
        raw_error = result.get("stderr") or result.get("error") or "Git operation failed."
        clean_msg = sanitize_user_error(str(raw_error), tool_context="Git operation")
        return f"❌ {clean_msg}"
    return str(result)


FORMATTERS = {
    "python": format_python,
    "filesystem": format_filesystem,
    "project_search": format_project_search,
    "code_intelligence": format_code_intelligence,
    "terminal": format_terminal,
    "git": format_git,
}


def format_tool_response(tool_name, action, result):

    formatter = FORMATTERS.get(tool_name)

    if formatter:
        return formatter(action, result)

    if isinstance(result, dict) and not result.get("success", True):
        error = result.get("error") or result.get("stderr") or "Operation failed"
        return f"❌ {sanitize_user_error(str(error), tool_context=tool_name)}"

    return str(result)

