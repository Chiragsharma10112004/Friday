import logging
from app.core.brain.manager import process_message

from app.core.runtime.orchestrator import process_tools
from app.core.runtime.responder import generate_tool_response

from app.memory.database import SessionLocal
from app.memory.repository import (
    save_message,
    get_recent_messages
)
from app.memory.memory_manager import (
    process_memory,
    build_memory_context
)

logger = logging.getLogger("friday.chat")

MAX_AGENT_STEPS = 10


def generate_response(message: str) -> str:
    db = SessionLocal()
    try:
        # 1. Record incoming user message immediately
        save_message(db, "user", message)

        # 2. Learn permanent facts into memory
        try:
            process_memory(db, message)
        except Exception as e:
            logger.debug("Memory learning error: %s", e)

        previous_steps = ""
        final_tool_output = None

        # 3. Agent Tool Loop
        for _ in range(MAX_AGENT_STEPS):
            try:
                tool_output = process_tools(
                    message=message,
                    previous_steps=previous_steps
                )
            except Exception as e:
                logger.debug("Tool processing error: %s", e)
                tool_output = None

            if tool_output is None:
                break

            previous_steps = tool_output.get("history", "")
            final_tool_output = tool_output

        # 4. If tools were used
        if final_tool_output:
            try:
                reply = generate_tool_response(final_tool_output)
            except Exception as e:
                logger.debug("Tool response generation error: %s", e)
                reply = f"Executed {final_tool_output.get('plan', {}).get('tool')}: {final_tool_output.get('result')}"

            save_message(db, "assistant", reply)
            return reply

        # 5. Normal Conversation with History & Memory
        history = get_recent_messages(db)
        memory_context = build_memory_context(db)

        try:
            reply = process_message(
                history,
                memory_context
            )
        except Exception as err:
            logger.warning("All AI providers failed: %s", err)
            # Safe fallback if LLM is offline or times out
            msg_lower = message.lower()
            if "name" in msg_lower and ("what" in msg_lower or "who" in msg_lower):
                if memory_context and "name:" in memory_context.lower():
                    for line in memory_context.split("\n"):
                        if line.lower().startswith("name:"):
                            reply = f"Based on your stored profile, your name is {line.split(':', 1)[1].strip()}."
                            break
                    else:
                        reply = "Your name is not provided in stored memory or profile."
                else:
                    reply = "Your name is not provided in stored memory or profile."
            elif "favorite" in msg_lower and "language" in msg_lower:
                if memory_context and "favorite_language:" in memory_context.lower():
                    for line in memory_context.split("\n"):
                        if "favorite_language:" in line.lower():
                            reply = f"Your favorite programming language is {line.split(':', 1)[1].strip()}."
                            break
                    else:
                        reply = "Your favorite programming language is not stored in memory."
                else:
                    reply = "Your favorite programming language is not stored in memory."
            elif "health" in msg_lower and "application" in msg_lower:
                if memory_context and "Application Health Summary:" in memory_context:
                    reply = "Here is the summary of your active applications:\n" + "\n".join(
                        [l for l in memory_context.split("\n") if "Health" in l or "Total Applications" in l or l.startswith("-")]
                    )
                else:
                    reply = "You currently have no active applications tracked in your pipeline."
            else:
                reply = "I am standing by. (Note: AI model provider is currently offline or unreachable, but your message and context are saved.)"

        save_message(db, "assistant", reply)
        return reply

    finally:
        db.close()
