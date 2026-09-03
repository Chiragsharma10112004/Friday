from app.core.editor.editor import edit_function
from app.core.editor.retry import repair_code
from app.core.editor.validator import validate_ast


class EditorAgent:
    """
    High-level interface for all code editing operations.
    """

    def edit(
        self,
        function_name: str,
        instruction: str,
        preview: bool = True,
    ):

        result = edit_function(
            function_name=function_name,
            instruction=instruction,
            preview=preview,
        )

        if not result.get("success"):
            return result

        validation = validate_ast(
            result["updated_function"]
        )

        if validation["valid"]:
            return result

        repaired = repair_code(
            original_prompt=instruction,
            generated_code=result["updated_function"],
        )

        if not repaired["success"]:
            return repaired

        result["updated_function"] = repaired["code"]

        return result
