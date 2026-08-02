from app.core.providers.ollama import generate


def process_message(messages, memory_context=""):
    return generate(messages, memory_context)
