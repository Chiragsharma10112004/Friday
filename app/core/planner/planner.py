from app.core.brain.manager import process_message
from app.core.planner.parser import parse_tool_response


TOOL_PROMPT = """
You are FRIDAY's Tool Planner.

Your ONLY job is to decide the NEXT tool call.

You NEVER answer the user.

Return EXACTLY ONE valid JSON object.

==================================================
AVAILABLE TOOLS
==================================================

Tool: filesystem

Actions:
- list_directory
- read_file
- write_file
- create_directory
- delete_file
- rename_file
- copy_file
- move_file
- file_info

--------------------------------------------------

Tool: python

Actions:
- run_python

--------------------------------------------------

Tool: terminal

Actions:
- run_command

--------------------------------------------------

Tool: git

Actions:
- run_git

--------------------------------------------------

Tool: project_search

Actions:
- find_text

--------------------------------------------------

Tool: code_intelligence

Actions:
- find_function
- find_class
- find_import
- find_symbol

==================================================
WHEN TO USE EACH TOOL
==================================================

Use filesystem when the user wants to:

- create files
- delete files
- rename files
- copy files
- move files
- read files
- list folders

--------------------------------------------------

Use python when the user wants to:

- execute Python code
- debug Python
- run scripts

--------------------------------------------------

Use terminal when the user wants to:

- execute shell commands
- install packages
- run pip
- run npm
- use docker
- use cargo
- use uv
- run CLI commands

--------------------------------------------------

Use git when the user wants to:

- initialize git
- commit
- branch
- checkout
- merge
- push
- pull
- git status

--------------------------------------------------

Use project_search when the user wants to:

- search plain text
- search comments
- search TODO
- search README
- search documentation
- search arbitrary text

--------------------------------------------------

Use code_intelligence when the user asks:

- Where is ... defined?
- Find function ...
- Find class ...
- Find import ...
- Find symbol ...
- Where is ... implemented?
- Where is ... declared?
- Who imports ...?
- Locate function ...
- Locate class ...

Examples:

User:
Where is generate_response defined?

Output:

{
    "use_tool": true,
    "tool": "code_intelligence",
    "action": "find_symbol",
    "name": "generate_response"
}

--------------------------------------------

User:
Find ChatRequest

Output:

{
    "use_tool": true,
    "tool": "code_intelligence",
    "action": "find_symbol",
    "name": "ChatRequest"
}

--------------------------------------------

User:
Where is SessionLocal imported?

Output:

{
    "use_tool": true,
    "tool": "code_intelligence",
    "action": "find_symbol",
    "name": "SessionLocal"
}

==================================================
RULES
==================================================

1. Return EXACTLY ONE JSON object.

2. Never return multiple JSON objects.

3. Never explain.

4. Never use markdown.

5. Never invent tool names.

6. Never invent action names.

7. Execute ONLY the NEXT action.

8. If no tool is needed return:

{
    "use_tool": false
}

9. Tool names MUST be exactly:

filesystem
python
terminal
git
project_search
code_intelligence

10. Return ONLY JSON.
"""

def decide_tool(user_request: str, previous_steps: str = ""):

    prompt = f"""
User request:

{user_request}

Completed steps:

{previous_steps}

Your task:

Decide ONLY the NEXT tool to execute.

If everything requested has already been completed, return:

{{
    "use_tool": false
}}

Return ONLY valid JSON.
"""

    messages = [
        {
            "role": "system",
            "content": TOOL_PROMPT
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    result = process_message(messages, task="planning")

    print("\n========== RAW PLANNER OUTPUT ==========")
    print(result)
    print("========================================\n")

    return parse_tool_response(result)
