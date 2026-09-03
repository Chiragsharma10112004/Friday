from pathlib import Path

SEARCH_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".html",
    ".css",
    ".js",
    ".ts",
}

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".idea",
    ".vscode",
}


def find_text(text: str, root: str = "."):
    """
    Search all supported source files in the project for a given text.
    """

    matches = []

    root_path = Path(root)

    for file in root_path.rglob("*"):

        if any(part in IGNORE_DIRS for part in file.parts):
            continue

        if not file.is_file():
            continue

        if file.suffix.lower() not in SEARCH_EXTENSIONS:
            continue

        try:
            with open(file, "r", encoding="utf-8", errors="ignore") as f:

                for line_number, line in enumerate(f, start=1):

                    if text in line:

                        matches.append(
                            {
                                "file": str(file),
                                "line": line_number,
                                "content": line.strip(),
                            }
                        )

        except Exception:
            continue

    return {
        "success": True,
        "query": text,
        "matches": matches,
    }
