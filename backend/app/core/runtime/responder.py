from app.core.brain.manager import process_message
from app.core.runtime.formatter import format_tool_response


def generate_tool_response(tool_output):
    """
    Format tool responses directly without sending them to the LLM.
    """

    return format_tool_response(
        tool_name=tool_output["plan"]["tool"],
        action=tool_output["plan"]["action"],
        result=tool_output["result"]
    )


def generate_chat_response(messages):
    """
    Generate a normal conversational response.
    """

    return process_message(messages, task="chat_response")
