from app.core.runtime.formatters.python_formatter import format_python
from app.core.runtime.formatters.filesystem_formatter import format_filesystem
from app.core.runtime.formatters.project_search_formatter import format_project_search
from app.core.runtime.formatters.code_intelligence_formatter import (
    format_code_intelligence,
)


FORMATTERS = {
    "python": format_python,
    "filesystem": format_filesystem,
    "project_search": format_project_search,
    "code_intelligence": format_code_intelligence,
}


def format_tool_response(tool_name, action, result):

    formatter = FORMATTERS.get(tool_name)

    if formatter:
        return formatter(action, result)

    return str(result)
