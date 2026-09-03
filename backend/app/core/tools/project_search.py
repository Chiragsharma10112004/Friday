from pathlib import Path


def find_text(
    query: str,
    path: str = ".",
    max_results: int = 20
):
    root = Path(path).resolve()
    results = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        if "__pycache__" in file_path.parts:
            continue

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:
                for line_number, line in enumerate(file, start=1):
                    if query.lower() in line.lower():
                        results.append({
                            "file": str(file_path),
                            "line": line_number,
                            "content": line.strip()
                        })

                        if len(results) >= max_results:
                            return results

        except (PermissionError, OSError):
            continue

    return results