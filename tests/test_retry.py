from app.core.editor.retry import repair_code

bad_code = """
def hello(
    print("Hello")
"""

result = repair_code(
    original_prompt="Create a hello function that prints Hello.",
    generated_code=bad_code,
)

print(result)
