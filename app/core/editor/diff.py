import difflib


def generate_diff(original: str, updated: str) -> str:
    """
    Generate a unified diff between two versions of text.
    """

    diff = difflib.unified_diff(
        original.splitlines(),
        updated.splitlines(),
        fromfile="original",
        tofile="updated",
        lineterm=""
    )

    return "\n".join(diff)
