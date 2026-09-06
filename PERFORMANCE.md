## Production Performance Notes

FRIDAY is designed to avoid unnecessary LLM/tool execution for simple conversational requests.

Current optimization priorities:
- Skip heavy planning for simple conversational queries
- Reduce unnecessary provider calls
- Keep provider timeouts bounded
- Preserve deterministic behavior for memory and application queries
- Validate performance changes with regression tests before deployment

Performance improvements will be measured against real production behavior after deployment.
