from app.core.editor.validator import validate_ast

good = """
def hello():
    print("Hello")
"""

bad = """
def hello(
    print("Hello")
"""

print("GOOD:")
print(validate_ast(good))

print()

print("BAD:")
print(validate_ast(bad))
