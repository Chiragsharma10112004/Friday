from openai import OpenAI
from app.config import OPENROUTER_API_KEY, OPENROUTER_MODEL

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

def chat(message: str):
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        max_tokens=512,
        temperature=0.7,
        messages=[
            {
                "role": "system",
                "content": "You are FRIDAY, a smart AI assistant."
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content
