import json

from app.core.providers.ollama import generate
from app.memory.repository import save_memory
from app.memory.repository import get_all_memory


def build_memory_context(db):

    memory = get_all_memory(db)

    if not memory:
        return ""

    context = "Known facts about the user:\n\n"

    for key, value in memory.items():
        context += f"{key}: {value}\n"

    return context


MEMORY_PROMPT = """
You are a memory extraction engine.

Extract ONLY permanent facts about the user.

Return ONLY valid JSON.

If there are no permanent facts return {}.

Example:

{
    "name":"Chirag Sharma",
    "favorite_language":"Python",
    "university":"GITAM University"
}
"""


def process_memory(db, message: str):

    messages = [
        {
            "role": "system",
            "content": MEMORY_PROMPT
        },
        {
            "role": "user",
            "content": message
        }
    ]

    result = generate(messages)

    try:

        memory = json.loads(result)

        for key, value in memory.items():
            save_memory(db, key, str(value))

    except Exception:
        pass
