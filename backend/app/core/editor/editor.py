import ast
from pathlib import Path
from app.core.editor.diff import generate_diff
from app.core.brain.manager import process_message

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".idea",
    ".vscode",
}


def extract_function(function_name: str, root: str = "."):
    """
    Locate a function using the AST and return only its source code.
    """

    root_path = Path(root)

    for file in root_path.rglob("*.py"):

        if any(part in IGNORE_DIRS for part in file.parts):
            continue

        try:
            source = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

        except Exception:
            continue

        lines = source.splitlines()

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef) and node.name == function_name:

                start = node.lineno - 1

                end = node.end_lineno

                return {
                    "success": True,
                    "file": str(file),
                    "line": node.lineno,
                    "start": start,
                    "end": end,
                    "function": function_name,
                    "source": "\n".join(lines[start:end]),
                }

    return {
        "success": False,
        "error": f"Function '{function_name}' not found."
    }


def replace_function(
    function_name: str,
    new_source: str,
    root: str = ".",
    preview: bool = True,
):
    """
    Replace ONLY one function.

    preview=True:
        Returns a preview and diff without modifying the file.

    preview=False:
        Writes the updated file.
    """

    result = extract_function(function_name, root)

    if not result["success"]:
        return result

    path = Path(result["file"])

    original_file = path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    lines = original_file.splitlines()

    updated_lines = (
        lines[:result["start"]]
        + new_source.splitlines()
        + lines[result["end"]:]
    )

    updated_source = "\n".join(updated_lines)

    diff = generate_diff(
        result["source"],
        new_source
    )

    if preview:

        return {
            "success": True,
            "preview": True,
            "file": str(path),
            "original_function": result["source"],
            "updated_function": new_source,
            "diff": diff,
            "updated_source": updated_source,
        }

    path.write_text(
        updated_source,
        encoding="utf-8"
    )

    return {
        "success": True,
        "preview": False,
        "file": str(path),
    }


def edit_function(
    function_name: str,
    instruction: str,
    root: str = ".",
    preview: bool = True,
):
    """
    Edit a single function using the LLM.
    """

    extracted = extract_function(function_name, root)

    if not extracted["success"]:
        return extracted

    prompt = f"""
You are an expert Python engineer.

Modify ONLY the following function.

Rules:

- Keep the same function name.
- Do not explain.
- Do not use markdown.
- Return ONLY valid Python code.
- Return ONLY the updated function.

Instruction:

{instruction}

Function:

{extracted["source"]}
"""

    messages = [
        {
            "role": "user",
            "content": prompt
        }
    ]

    edited_function = process_message(messages, task="code_editor").strip()

    return replace_function(
        function_name=function_name,
        new_source=edited_function,
        root=root,
        preview=preview,
    )
