import subprocess


def run_command(command: str, timeout: int = 30):
    """
    Execute a terminal command and return the result.

    Args:
        command: Terminal command to execute.
        timeout: Maximum execution time in seconds.
    """

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={
                **__import__("os").environ,
                "TERM": "dumb",
                "NO_COLOR": "1"
            }
)

        return {
            "success": result.returncode == 0,
            "command": command,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "command": command,
            "error": f"Command timed out after {timeout} seconds."
        }

    except Exception as e:
        return {
            "success": False,
            "command": command,
            "error": str(e)
        }
