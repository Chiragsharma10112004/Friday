from app.core.brain.manager import process_message
from app.core.editor.validator import validate_ast

MAX_RETRIES = 3


def clean_code(code: str) -> str:
    """
    Remove markdown code fences from LLM output.
    """

    code = code.strip()

    if code.startswith("```python"):
        code = code[len("```python"):]

    elif code.startswith("```"):
        code = code[len("```"):]

    if code.endswith("```"):
        code = code[:-3]

    return code.strip()


def repair_code(
    original_prompt: str,
    generated_code: str,
):
    """
    Keep asking the LLM until valid Python is produced.
    """

    current = clean_code(generated_code)

    for attempt in range(MAX_RETRIES):

        validation = validate_ast(current)

        if validation["valid"]:
            return {
                "success": True,
                "code": current,
                "attempts": attempt,
            }

        retry_prompt = f"""
The following Python function is invalid.

Syntax Error:
{validation["error"]}

Fix ONLY the syntax.

Rules:

- Return ONLY one valid Python function.
- Do NOT use markdown.
- Do NOT use ```python.
- Do NOT explain anything.
- Keep the original function name.

Original Request:

{original_prompt}

Invalid Function:

{current}
"""

        response = process_message(
            [
                {
                    "role": "user",
                    "content": retry_prompt,
                }
            ],
            task="code_repair"
        )

        current = clean_code(response)

    return {
        "success": False,
        "error": "Unable to generate valid code.",
        "last_output": current,
    }
