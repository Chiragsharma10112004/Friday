import json
import re


def parse_tool_response(response: str):
    try:
        return json.loads(response)

    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response, re.DOTALL)

        if match:
            return json.loads(match.group())

        raise ValueError("Invalid JSON returned by planner.")
