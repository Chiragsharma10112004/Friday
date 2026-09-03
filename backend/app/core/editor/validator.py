import ast


def validate_syntax(code: str):
    """
    Validate that the supplied code is valid Python.
    """

    try:
        ast.parse(code)

        return {
            "success": True,
            "valid": True,
        }

    except SyntaxError as e:

        return {
            "success": True,
            "valid": False,
            "error": str(e),
            "line": e.lineno,
            "offset": e.offset,
        }


def validate_function(code: str):
    """
    Validate that the code represents exactly one Python function.
    """

    syntax = validate_syntax(code)

    if not syntax["valid"]:
        return syntax

    tree = ast.parse(code)

    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    ]

    if len(functions) != 1:
        return {
            "success": True,
            "valid": False,
            "error": "Expected exactly one function."
        }

    return {
        "success": True,
        "valid": True,
    }


def validate_ast(code: str):
    """
    Perform all validation checks.
    """

    return validate_function(code)
