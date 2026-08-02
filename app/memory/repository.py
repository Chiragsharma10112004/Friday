from sqlalchemy.orm import Session

from app.memory.models import ChatHistory, UserMemory


def save_message(db: Session, role: str, message: str):
    chat = ChatHistory(
        role=role,
        message=message
    )

    db.add(chat)
    db.commit()


def get_recent_messages(db: Session, limit: int = 20):
    messages = (
        db.query(ChatHistory)
        .order_by(ChatHistory.id.desc())
        .limit(limit)
        .all()
    )

    messages.reverse()

    return [
        {
            "role": msg.role,
            "content": msg.message
        }
        for msg in messages
    ]


# --------------------------
# Long-Term Memory Functions
# --------------------------

def save_memory(db: Session, key: str, value: str):
    memory = db.query(UserMemory).filter(UserMemory.key == key).first()

    if memory:
        memory.value = value
    else:
        memory = UserMemory(
            key=key,
            value=value
        )
        db.add(memory)

    db.commit()


def get_memory(db: Session, key: str):
    memory = db.query(UserMemory).filter(UserMemory.key == key).first()

    if memory:
        return memory.value

    return None


def get_all_memory(db: Session):
    memories = db.query(UserMemory).all()

    return {
        memory.key: memory.value
        for memory in memories
    }
