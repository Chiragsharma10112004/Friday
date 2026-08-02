from app.core.editor.diff import generate_diff

old = """
def hello():
    print("Hello")
"""

new = """
def hello():
    print("Hello FRIDAY")
"""

print(generate_diff(old, new))
