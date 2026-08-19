import ast
from pathlib import Path


def find_symbol(
    symbol: str,
    path: str = "."
):
    root = Path(path).resolve()
    results = []

    for file_path in root.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue

        try:
            source = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef
                    )
                ):
                    if node.name == symbol:
                        results.append({
                            "file": str(file_path),
                            "symbol": node.name,
                            "type": type(node).__name__,
                            "line": node.lineno
                        })

        except (
            SyntaxError,
            PermissionError,
            OSError
        ):
            continue

    return results