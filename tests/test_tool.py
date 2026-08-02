from app.core.runtime.manager import execute_tool

result = execute_tool(
    "terminal",
    "run_command",
    command="dir"
)

print(result)
