import ast
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.core.code_intelligence.schemas import (
    SymbolDefinition,
    FileInspection,
    WorkspaceMap,
)

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".idea",
    ".vscode",
}


class CodeAnalyzer:
    """
    Analyzes Python repository structure, building symbol indexes,
    import graphs, and AST-level inspections.
    """

    @classmethod
    def inspect_file(cls, file_path: Path) -> Optional[FileInspection]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content)
            lines = content.splitlines()

            functions: List[str] = []
            classes: List[str] = []
            imports: List[str] = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for alias in node.names:
                        imports.append(f"{mod}.{alias.name}")

            return FileInspection(
                path=str(file_path),
                name=file_path.name,
                size_bytes=len(content.encode("utf-8")),
                lines_count=len(lines),
                symbols_count=len(functions) + len(classes),
                functions=functions,
                classes=classes,
                imports=imports,
            )
        except Exception:
            return None

    @classmethod
    def analyze_workspace(cls, root: str = ".") -> WorkspaceMap:
        root_path = Path(root).resolve()
        files: List[FileInspection] = []
        symbol_index: Dict[str, List[str]] = defaultdict(list)
        total_lines = 0

        for file in root_path.rglob("*.py"):
            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            insp = cls.inspect_file(file)
            if insp:
                files.append(insp)
                total_lines += insp.lines_count
                rel_path = str(file.relative_to(root_path))
                for fn in insp.functions:
                    symbol_index[fn].append(rel_path)
                for cl in insp.classes:
                    symbol_index[cl].append(rel_path)

        return WorkspaceMap(
            root_path=str(root_path),
            total_files=len(files),
            total_lines=total_lines,
            files=files,
            symbol_index=dict(symbol_index),
        )

    @classmethod
    def lookup_symbol(cls, symbol_name: str, root: str = ".") -> List[SymbolDefinition]:
        root_path = Path(root).resolve()
        results: List[SymbolDefinition] = []

        for file in root_path.rglob("*.py"):
            if any(part in IGNORE_DIRS for part in file.parts):
                continue

            try:
                content = file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == symbol_name:
                    sym_type = "function" if isinstance(node, ast.FunctionDef) else "class"
                    params = []
                    if isinstance(node, ast.FunctionDef):
                        params = [a.arg for a in node.args.args]

                    doc = ast.get_docstring(node)
                    results.append(
                        SymbolDefinition(
                            name=node.name,
                            symbol_type=sym_type,
                            file=str(file.relative_to(root_path)),
                            line=node.lineno,
                            docstring=doc,
                            parameters=params,
                        )
                    )

        return results
