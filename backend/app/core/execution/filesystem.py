from pathlib import Path
import shutil


def list_directory(path="."):
    try:
        items = []

        for item in Path(path).iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file"
            })

        return {
            "success": True,
            "items": items
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def read_file(path):
    try:
        text = Path(path).read_text(encoding="utf-8")

        return {
            "success": True,
            "content": text
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def write_file(path, content):
    try:
        Path(path).write_text(content, encoding="utf-8")

        return {
            "success": True,
            "message": f"{path} written successfully."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_directory(path):
    try:
        Path(path).mkdir(parents=True, exist_ok=True)

        return {
            "success": True,
            "message": f"Directory '{path}' created."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def delete_file(path):
    try:
        Path(path).unlink()

        return {
            "success": True,
            "message": f"{path} deleted."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def rename_file(source, destination):
    try:
        Path(source).rename(destination)

        return {
            "success": True,
            "message": "Rename successful."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def copy_file(source, destination):
    try:
        shutil.copy2(source, destination)

        return {
            "success": True,
            "message": "Copy successful."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def move_file(source, destination):
    try:
        shutil.move(source, destination)

        return {
            "success": True,
            "message": "Move successful."
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def file_info(path):
    try:
        p = Path(path)

        return {
            "success": True,
            "name": p.name,
            "size": p.stat().st_size,
            "is_file": p.is_file(),
            "is_directory": p.is_dir(),
            "absolute_path": str(p.resolve())
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
