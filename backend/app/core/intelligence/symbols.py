import ast
from pathlib import Path


IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".idea",
    ".vscode",
}


def _python_files(root="."):
    root_path = Path(root)

    for file in root_path.rglob("*.py"):

        if any(part in IGNORE_DIRS for part in file.parts):
            continue

        yield file


def find_function(name: str, root: str = "."):

    matches = []

    for file in _python_files(root):

        try:
            tree = ast.parse(
                file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
            )
        except Exception:
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef) and node.name == name:

                matches.append(
                    {
                        "file": str(file),
                        "line": node.lineno,
                        "name": node.name,
                        "type": "function",
                    }
                )

    return {
        "success": True,
        "function": name,
        "matches": matches,
    }


def find_class(name: str, root: str = "."):

    matches = []

    for file in _python_files(root):

        try:
            tree = ast.parse(
                file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
            )
        except Exception:
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef) and node.name == name:

                matches.append(
                    {
                        "file": str(file),
                        "line": node.lineno,
                        "name": node.name,
                        "type": "class",
                    }
                )

    return {
        "success": True,
        "class": name,
        "matches": matches,
    }


def find_import(name: str, root: str = "."):

    matches = []

    for file in _python_files(root):

        try:
            tree = ast.parse(
                file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
            )
        except Exception:
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:

                    if alias.name.endswith(name):

                        matches.append(
                            {
                                "file": str(file),
                                "line": node.lineno,
                                "import": alias.name,
                                "type": "import",
                            }
                        )

            elif isinstance(node, ast.ImportFrom):

                for alias in node.names:

                    if alias.name == name:

                        module = node.module or ""

                        matches.append(
                            {
                                "file": str(file),
                                "line": node.lineno,
                                "import": f"{module}.{alias.name}",
                                "type": "import",
                            }
                        )

    return {
        "success": True,
        "import": name,
        "matches": matches,
    }

def find_symbol(name: str, root: str = "."):
    """
    Try to locate a symbol in the project.

    Search order:
    1. Function
    2. Class
    3. Import
    """

    result = find_function(name, root)

    if result["matches"]:
        return {
            "success": True,
            "symbol": name,
            "symbol_type": "function",
            "matches": result["matches"],
        }

    result = find_class(name, root)

    if result["matches"]:
        return {
            "success": True,
            "symbol": name,
            "symbol_type": "class",
            "matches": result["matches"],
        }

    result = find_import(name, root)

    if result["matches"]:
        return {
            "success": True,
            "symbol": name,
            "symbol_type": "import",
            "matches": result["matches"],
        }

    return {
        "success": True,
        "symbol": name,
        "symbol_type": None,
        "matches": [],
    }
