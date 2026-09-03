import subprocess


def run_git(command: str):
    """
    Execute a git command and return the result.
    Example:
        run_git("status")
        run_git("init")
        run_git("branch")
    """

    try:
        result = subprocess.run(
            ["git"] + command.split(),
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success": result.returncode == 0,
            "command": f"git {command}",
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "command": f"git {command}",
            "error": "Git command timed out after 30 seconds."
        }

    except Exception as e:
        return {
            "success": False,
            "command": f"git {command}",
            "error": str(e)
        }
