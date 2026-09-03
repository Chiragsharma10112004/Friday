def format_filesystem(action, result):
    """
    Format filesystem tool responses.
    """

    if not result.get("success"):
        return (
            "❌ Filesystem Error\n\n"
            f"{result.get('error', 'Unknown error')}"
        )

    if action == "list_directory":

        items = result.get("items", [])

        if not items:
            return "📁 Directory is empty."

        lines = []

        for item in items:

            icon = "📁" if item["type"] == "directory" else "📄"

            lines.append(f"{icon} {item['name']}")

        return (
            "📁 Directory Contents\n\n"
            + "\n".join(lines)
        )

    elif action == "read_file":

        return (
            "📄 File Content\n\n"
            f"{result.get('content', '')}"
        )

    elif action in [
        "write_file",
        "create_directory",
        "delete_file",
        "rename_file",
        "copy_file",
        "move_file",
    ]:

        return (
            "✅ Success\n\n"
            f"{result.get('message', '')}"
        )

    elif action == "file_info":

        return (
            "📄 File Information\n\n"
            f"Name: {result.get('name')}\n"
            f"Size: {result.get('size')} bytes\n"
            f"File: {result.get('is_file')}\n"
            f"Directory: {result.get('is_directory')}\n"
            f"Path: {result.get('absolute_path')}"
        )

    return str(result)
