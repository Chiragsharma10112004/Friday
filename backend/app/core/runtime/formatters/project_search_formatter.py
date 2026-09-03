def format_project_search(action, result):

    if not result.get("success"):
        return "❌ Search failed."

    matches = result.get("matches", [])

    if not matches:
        return f"No matches found for '{result['query']}'."

    lines = [
        f"Found {len(matches)} match(es) for '{result['query']}':",
        ""
    ]

    for match in matches:
        lines.append(
            f"📄 {match['file']}  (Line {match['line']})"
        )
        lines.append(f"    {match['content']}")
        lines.append("")

    return "\n".join(lines)
