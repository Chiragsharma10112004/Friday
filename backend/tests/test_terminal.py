from app.core.runtime.manager import execute_tool


result = execute_tool(
    tool_name="terminal",
    action="run_command",
    command="echo Hello FRIDAY"
)

print(result)
