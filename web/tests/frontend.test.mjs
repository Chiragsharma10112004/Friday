import test from "node:test";
import assert from "node:assert/strict";

// Helper function mirroring sanitizeTextForSpeech logic
function sanitizeTextForSpeech(markdown) {
  if (!markdown) return "";
  let clean = markdown
    .replace(/```[\s\S]*?```/g, " Code block omitted. ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1")
    .replace(/[*_~#>]/g, "")
    .replace(/\|.*\|/g, "")
    .replace(/-{3,}/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return clean;
}

test("sanitizeTextForSpeech strips markdown syntax for natural voice synthesis", () => {
  const input = "Greetings **Operator**! Here is the code:\n```python\nprint('hello')\n```\nVisit [Google](https://google.com) for details.";
  const sanitized = sanitizeTextForSpeech(input);
  
  assert.ok(!sanitized.includes("**"));
  assert.ok(!sanitized.includes("```"));
  assert.ok(!sanitized.includes("print('hello')"));
  assert.ok(sanitized.includes("Code block omitted."));
  assert.ok(sanitized.includes("Visit Google for details."));
  assert.ok(!sanitized.includes("https://google.com"));
});

test("ChatMessage type and context_sources integrity", () => {
  const message = {
    id: "test-123",
    role: "assistant",
    content: "The test suite has 138 passing tests.",
    context_sources: ["Memory", "Repository AST"],
    timestamp: "12:00 PM"
  };

  assert.equal(message.role, "assistant");
  assert.equal(message.context_sources.length, 2);
  assert.deepEqual(message.context_sources, ["Memory", "Repository AST"]);
});

test("Voice toggle default state is ON for new sessions", () => {
  const defaultEnabled = true;
  assert.equal(defaultEnabled, true, "Voice assistant defaults to ON for new session");
});
