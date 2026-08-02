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


MAX_AGENT_STEPS = 10


def generate_response(message: str) -> str:

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Learn memory
        # ------------------------------------------
        process_memory(db, message)

        previous_steps = ""

        final_tool_output = None

        # ------------------------------------------
        # Agent Loop
        # ------------------------------------------

        for _ in range(MAX_AGENT_STEPS):

            tool_output = process_tools(
                message=message,
                previous_steps=previous_steps
            )

            if tool_output is None:
                break

            previous_steps = tool_output["history"]

            final_tool_output = tool_output

        # ------------------------------------------
        # If tools were used
        # ------------------------------------------

        if final_tool_output:

            reply = generate_tool_response(final_tool_output)

            save_message(db, "user", message)
            save_message(db, "assistant", reply)

            return reply

        # ------------------------------------------
        # Normal Conversation
        # ------------------------------------------

        save_message(db, "user", message)

        history = get_recent_messages(db)

        memory_context = build_memory_context(db)

        reply = process_message(
            history,
            memory_context
        )

        save_message(db, "assistant", reply)

        return reply

    finally:
        db.close()
