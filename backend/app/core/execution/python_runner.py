import subprocess
import tempfile
import os


def run_python(code: str):
    try:
        # Create a temporary Python file
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name

        # Execute it
        result = subprocess.run(
            ["python", temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Clean up
        os.remove(temp_path)

        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
