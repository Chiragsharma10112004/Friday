from ollama import chat as ollama_chat

MODEL = "qwen2.5:7b"


SYSTEM_PROMPT = """
You are FRIDAY.

Never say you are Qwen.

You are Chirag's personal AI assistant.

Be intelligent, concise, proactive and helpful.
"""


def generate(messages, memory_context=""):
    response = ollama_chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT + "\n\n" + memory_context
            },
            *messages
        ]
    )

    return response["message"]["content"]
