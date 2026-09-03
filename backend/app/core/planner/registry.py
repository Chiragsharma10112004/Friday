from app.core.execution.filesystem import (
    list_directory,
    read_file,
    write_file,
    create_directory,
    delete_file,
    rename_file,
    copy_file,
    move_file,
    file_info,
)

from app.core.execution.python_runner import run_python
from app.core.execution.terminal import run_command
from app.core.execution.git import run_git

from app.core.intelligence.search import find_text
from app.core.intelligence.symbols import find_symbol


TOOLS = {
    "filesystem": {
        "list_directory": list_directory,
        "read_file": read_file,
        "write_file": write_file,
        "create_directory": create_directory,
        "delete_file": delete_file,
        "rename_file": rename_file,
        "copy_file": copy_file,
        "move_file": move_file,
        "file_info": file_info,
    },

    "python": {
        "run_python": run_python,
    },

    "terminal": {
        "run_command": run_command,
    },

    "git": {
        "run_git": run_git,
    },

    "project_search": {
        "find_text": find_text,
    },

    "code_intelligence": {
        "find_symbol": find_symbol,
    },
}
