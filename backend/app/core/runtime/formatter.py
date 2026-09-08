from app.core.runtime.formatters.python_formatter import format_python
from app.core.runtime.formatters.filesystem_formatter import format_filesystem
from app.core.runtime.formatters.project_search_formatter import format_project_search
from app.core.runtime.formatters.code_intelligence_formatter import (
    format_code_intelligence,
)


def format_terminal(action, result):
    if isinstance(result, dict):
        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            return stdout if stdout else "Command executed successfully with no output."
        error = result.get("stderr") or result.get("error") or "Command execution failed."
        return f"❌ Command Failed:\n{error}"
    return str(result)


def format_git(action, result):
    if isinstance(result, dict):
        if result.get("success"):
            stdout = result.get("stdout", "").strip()
            return stdout if stdout else "Git operation completed successfully."
        error = result.get("stderr") or result.get("error") or "Git operation failed."
        return f"❌ Git Failed:\n{error}"
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

    return str(result)

