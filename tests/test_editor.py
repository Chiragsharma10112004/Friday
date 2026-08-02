from app.core.editor.editor import edit_function

result = edit_function(
    function_name="generate_response",
    instruction="Add a print statement saying 'FRIDAY STARTED' at the beginning of the function.",
    preview=True,
)

print(result["diff"])
