from app.core.brain.manager import process_message
from app.core.planner.parser import parse_tool_response
from app.core.planner.registry import TOOLS


TOOL_PROMPT = """You are FRIDAY's Tool Planner.

Your job is to decide whether the user's request requires executing a local system/code tool or if it should be answered directly as a conversational/knowledge response with NO tools.

==================================================
CRITICAL DISTINCTION: QUESTIONS ABOUT TOOLS vs REQUESTS TO EXECUTE TOOLS
==================================================

1. Questions ABOUT a tool, command, technology, or syntax MUST return {"use_tool": false}.
   When the user is asking for explanations, definitions, tutorials, advice, or conceptual information:
   - "What does git status mean?" -> {"use_tool": false}
   - "Explain how ls works" -> {"use_tool": false}
   - "What is a terminal?" -> {"use_tool": false}
   - "How does Git work?" -> {"use_tool": false}
   - "What is the difference between git fetch and git pull?" -> {"use_tool": false}
   - "What does rm -rf do?" -> {"use_tool": false}
   - "How do I use pytest?" -> {"use_tool": false}
   - "What is docker?" -> {"use_tool": false}
   - "Explain the filesystem" -> {"use_tool": false}
   - "What is Python?" -> {"use_tool": false}

2. Explicit REQUESTS TO EXECUTE, RUN, INSPECT, OR MODIFY the local system/codebase should return {"use_tool": true, ...}:
   - "run git status" -> {"use_tool": true, "tool": "git", "action": "run_git", "command": "status"}
   - "list files in this directory" -> {"use_tool": true, "tool": "filesystem", "action": "list_directory", "path": "."}
   - "execute command npm test" -> {"use_tool": true, "tool": "terminal", "action": "run_command", "command": "npm test"}
   - "where is generate_response defined?" -> {"use_tool": true, "tool": "code_intelligence", "action": "find_symbol", "name": "generate_response"}
   - "search for TODO in the codebase" -> {"use_tool": true, "tool": "project_search", "action": "find_text", "query": "TODO"}
   - "check my GitHub repository" -> {"use_tool": true, "tool": "git", "action": "run_git", "command": "status"}

==================================================
CRITICAL RULE: WHEN TO USE NO TOOL ({"use_tool": false})
==================================================

You MUST return {"use_tool": false} for:
1. General knowledge, factual, trivia, geography, history, science, or definition questions (e.g., "who is the prime minister of india", "what is the capital of France", "who founded Apple", "what is python", "explain quantum computing", "how does a compiler work").
2. Questions ABOUT tools, commands, or concepts (e.g., "what does git status mean?", "explain how ls works").
3. Conversational greetings, pleasantries, questions about FRIDAY/identity/capabilities (e.g., "hello", "hi", "how are you", "who are you", "what can you do", "tell me a joke", "write a poem").
4. Personal / memory questions (e.g., "what is my name", "what is my favorite programming language", "summarize my applications").
5. Requests asking to write code, provide examples, explain algorithms, or debug conceptual code in text (where the user is NOT asking to create/edit local files or run local scripts).
6. When all requested steps have already been completed in "Completed steps".

STRICT PROHIBITION:
- NEVER use the terminal tool to "echo", "printf", or output text answers to questions. The terminal tool is strictly for legitimate CLI/shell commands requested by the user.
- NEVER use the python tool to print answers to factual questions.

==================================================
AVAILABLE TOOLS AND ACTIONS
==================================================

1. filesystem: list_directory, read_file, write_file, create_directory, delete_file, rename_file, copy_file, move_file, file_info
2. python: run_python
3. terminal: run_command
4. git: run_git
5. project_search: find_text
6. code_intelligence: find_symbol

==================================================
OUTPUT FORMAT
==================================================
Return EXACTLY ONE valid JSON object with no surrounding commentary or markdown.

If NO tool is needed:
{
    "use_tool": false
}

If a tool IS needed:
{
    "use_tool": true,
    "tool": "<tool_name>",
    "action": "<action_name>",
    ...kwargs
}
"""

EXPLICIT_EXECUTION_VERBS = (
    "run ", "execute ", "exec ", "launch ", "start ",
    "create file", "create directory", "create folder", "make file", "make directory", "make folder",
    "delete file", "delete directory", "delete folder", "remove file", "remove folder", "remove directory",
    "rename file", "rename folder", "rename directory",
    "copy file", "copy folder", "move file", "move folder",
    "list files", "list directory", "list folder", "show files", "show directory", "show folder",
    "check git", "check my git", "check repository", "check my repository", "check github", "check my github",
    "find symbol", "find function", "find class", "find import",
    "where is ", "who imports "
)

EXPLANATION_OR_INFO_PATTERNS = (
    "what is ", "what was ", "what are ", "what were ", "what does ", "what do ",
    "why is ", "why was ", "why are ", "why do ", "why does ", "why did ",
    "when was ", "when did ", "when is ",
    "how does ", "how do ", "how is ", "how can i ", "how to ",
    "can you explain ", "explain ", "tell me about ", "tell me a ",
    "give me an example of ", "describe ", "define ", "meaning of ",
    "difference between ", "what's the difference "
)

CONVERSATIONAL_PHRASES = {
    "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
    "how are you", "who are you", "what can you do", "help", "thanks", "thank you",
    "how is everything running today", "how is everything running today?"
}


def decide_tool(user_request: str, previous_steps: str = ""):
    clean_req = user_request.strip().lower()

    # Fast-path 1: Conversational greetings and pleasantries
    if clean_req in CONVERSATIONAL_PHRASES or clean_req.startswith(("hello", "hi ", "hey ", "good morning", "good evening", "good afternoon")):
        if not any(clean_req.startswith(verb) for verb in EXPLICIT_EXECUTION_VERBS):
            return {"use_tool": False}

    # Fast-path 2: Memory/profile and status queries
    if clean_req.startswith(("what is my", "what's my", "who am i", "summarize the health", "tell me about my", "summarize my")) and not any(
        clean_req.startswith(verb) for verb in EXPLICIT_EXECUTION_VERBS
    ):
        return {"use_tool": False}

    # Fast-path 3: Questions asking for explanations, definitions, tutorials, or concepts
    # Even if they mention tools/commands (e.g. "what does git status mean?", "explain how ls works", "what is a terminal?")
    if clean_req.startswith(EXPLANATION_OR_INFO_PATTERNS):
        # Unless it specifically contains an explicit execution phrase
        if not any(clean_req.startswith(verb) or f" {verb}" in clean_req for verb in ("where is ", "who imports ", "find symbol", "find function", "find class")):
            if not any(clean_req.startswith(verb) for verb in EXPLICIT_EXECUTION_VERBS):
                return {"use_tool": False}

    # Fast-path 4: General knowledge questions starting with "who is", "who was", "who discovered", etc.
    if clean_req.startswith(("who is ", "who was ", "who are ", "who were ", "who founded ", "who created ", "who discovered ", "who wrote ", "who invented ", "who built ", "who made ")):
        if not any(clean_req.startswith(verb) for verb in EXPLICIT_EXECUTION_VERBS):
            return {"use_tool": False}

    # Fast-path 5: Creative/conversational text generation (e.g. write a poem, write a story)
    if clean_req.startswith(("write a ", "write an ", "compose ", "draft ")) and not any(
        kw in clean_req for kw in ("file", "folder", "directory", "disk", "script", "save", "create file")
    ):
        if not any(clean_req.startswith(verb) for verb in EXPLICIT_EXECUTION_VERBS):
            return {"use_tool": False}


    prompt = f"""User request:

{user_request}

Completed steps:

{previous_steps}

Your task:

Decide ONLY the NEXT tool to execute.

If everything requested has already been completed, or if the user is asking a general question/conversation/explanation that requires no local system action, return:

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

    try:
        result = process_message(messages, task="planning")
        plan = parse_tool_response(result)
    except Exception:
        return {"use_tool": False}

    if not plan or not isinstance(plan, dict) or not plan.get("use_tool"):
        return {"use_tool": False}

    tool_name = plan.get("tool")
    action = plan.get("action")

    # Safety Guardrail 1: Validate tool and action exist in registry
    if not tool_name or tool_name not in TOOLS:
        return {"use_tool": False}
    if not action or action not in TOOLS[tool_name]:
        return {"use_tool": False}

    # Safety Guardrail 2: Reject hallucinated terminal commands using echo/printf to answer questions
    if tool_name == "terminal" and action == "run_command":
        cmd = str(plan.get("command", "")).strip()
        if not cmd:
            return {"use_tool": False}
        cmd_lower = cmd.lower()
        if cmd_lower.startswith(("echo ", "echo\t", "printf ", "cat <<", "echo.", "echo/")):
            if not any(redir in cmd for redir in (">", ">>", "|")):
                return {"use_tool": False}

    # Safety Guardrail 3: Reject hallucinated python prints answering questions
    if tool_name == "python" and action == "run_python":
        code = str(plan.get("code", "")).strip()
        if code.startswith("print(") and not any(kw in clean_req for kw in ("run", "execute", "script", "python", "test")):
            return {"use_tool": False}

    return plan


