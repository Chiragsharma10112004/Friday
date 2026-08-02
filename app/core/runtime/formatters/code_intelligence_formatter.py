def format_code_intelligence(action, result):

    if not result.get("success"):
        return "❌ Code intelligence failed."

    matches = result.get("matches", [])

    if not matches:
        return f"No symbol named '{result.get('symbol', '')}' was found."

    symbol_type = result.get("symbol_type", "symbol")

    lines = [
        f"Found {symbol_type}: '{result['symbol']}'",
        ""
    ]

    for match in matches:

        lines.append(
            f"📄 {match['file']} (Line {match['line']})"
        )

        if "name" in match:
            lines.append(f"Type: {match['type']}")
            lines.append(f"Name: {match['name']}")

        elif "import" in match:
            lines.append(f"Import: {match['import']}")

        lines.append("")

    return "\n".join(lines)
