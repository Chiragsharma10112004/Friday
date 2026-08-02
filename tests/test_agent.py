from app.core.editor.agent import EditorAgent

agent = EditorAgent()

result = agent.edit(
    function_name="generate_response",
    instruction="Add a print('FRIDAY STARTED') at the beginning of the function.",
    preview=True,
)

print(result["diff"])
