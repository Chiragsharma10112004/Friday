import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.planner.planner import decide_tool
from app.core.runtime.orchestrator import process_tools
from app.services.ai_service import generate_response
from app.memory.database import SessionLocal, Base, engine
from app.memory.models import UserMemory, ChatHistory



class ToolRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()
        self.db.query(UserMemory).delete()
        self.db.query(ChatHistory).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    # -------------------------------------------------------------------------
    # 1. Simple Knowledge & Factual Questions (Must NOT invoke tools)
    # -------------------------------------------------------------------------
    def test_01_knowledge_questions_bypass_tools(self):
        knowledge_queries = [
            "who is the prime of india",
            "who is the prime minister of india",
            "who is the president of the united states",
            "what is the capital of France",
            "what is photosynthesis",
            "explain quantum computing",
            "who discovered gravity",
            "why is the sky blue",
            "tell me a joke",
            "write a poem about space",
        ]
        for query in knowledge_queries:
            plan = decide_tool(query)
            self.assertFalse(
                plan.get("use_tool", False),
                f"Expected use_tool=False for knowledge query: '{query}', got: {plan}"
            )
            result = process_tools(query)
            self.assertIsNone(
                result,
                f"Expected process_tools to return None for '{query}', got: {result}"
            )

    # -------------------------------------------------------------------------
    # 2. Questions ABOUT Tools / Commands (Must NOT invoke tools)
    # -------------------------------------------------------------------------
    def test_02_questions_about_tools_bypass_tools(self):
        questions_about_tools = [
            "What does git status mean?",
            "Explain how ls works",
            "What is a terminal?",
            "How does Git work?",
            "What is Python?",
            "What does rm -rf do?",
            "How do I use pytest?",
            "What is Docker?",
            "Explain the difference between git fetch and git pull",
            "Can you explain how python decorators work?",
            "Tell me about terminal commands",
        ]
        for query in questions_about_tools:
            plan = decide_tool(query)
            self.assertFalse(
                plan.get("use_tool", False),
                f"Expected use_tool=False for question about tools: '{query}', got: {plan}"
            )
            result = process_tools(query)
            self.assertIsNone(
                result,
                f"Expected process_tools to return None for '{query}', got: {result}"
            )

    # -------------------------------------------------------------------------
    # 3. Conversational Greetings & Memory (Must NOT invoke tools)
    # -------------------------------------------------------------------------
    def test_03_conversational_and_memory_queries_bypass_tools(self):
        chat_queries = [
            "hello",
            "hi FRIDAY",
            "good morning",
            "how are you today",
            "who are you",
            "what can you do",
            "what is my name?",
            "what is my favorite programming language?",
            "summarize the health status of my active job applications",
        ]
        for query in chat_queries:
            plan = decide_tool(query)
            self.assertFalse(
                plan.get("use_tool", False),
                f"Expected use_tool=False for conversational query: '{query}', got: {plan}"
            )

    # -------------------------------------------------------------------------
    # 4. Safety Guardrails: Reject Hallucinated Tool Commands
    # -------------------------------------------------------------------------
    def test_04_terminal_echo_hallucination_rejected(self):
        # Mock planner returning an echo command to answer a question
        mock_raw_output = '{"use_tool": true, "tool": "terminal", "action": "run_command", "command": "echo The Prime Minister of India is Narendra Modi"}'
        with patch("app.core.planner.planner.process_message", return_value=mock_raw_output):
            plan = decide_tool("Tell me who is prime of india")
            self.assertFalse(
                plan.get("use_tool", False),
                "Terminal echo hallucination should be safely rejected by guardrail."
            )

    def test_05_python_print_hallucination_rejected(self):
        # Mock planner returning a python print answering a factual question
        mock_raw_output = '{"use_tool": true, "tool": "python", "action": "run_python", "code": "print(\'Paris\')"}'
        with patch("app.core.planner.planner.process_message", return_value=mock_raw_output):
            plan = decide_tool("What is the capital of France?")
            self.assertFalse(
                plan.get("use_tool", False),
                "Python print answering question should be safely rejected by guardrail."
            )

    def test_06_unknown_tool_or_action_rejected(self):
        mock_raw_output = '{"use_tool": true, "tool": "fake_tool", "action": "fake_action"}'
        with patch("app.core.planner.planner.process_message", return_value=mock_raw_output):
            plan = decide_tool("Run something")
            self.assertFalse(plan.get("use_tool", False))
            self.assertIsNone(process_tools("Run something"))

    # -------------------------------------------------------------------------
    # 5. Legitimate Tool Execution Requests (Must Invoke Tools)
    # -------------------------------------------------------------------------
    def test_07_legitimate_tool_requests_allowed(self):
        # 1. Code intelligence lookup
        mock_symbol_output = '{"use_tool": true, "tool": "code_intelligence", "action": "find_symbol", "name": "generate_response"}'
        with patch("app.core.planner.planner.process_message", return_value=mock_symbol_output):
            plan = decide_tool("where is generate_response defined?")
            self.assertTrue(plan.get("use_tool"))
            self.assertEqual(plan.get("tool"), "code_intelligence")
            self.assertEqual(plan.get("action"), "find_symbol")

        # 2. Filesystem listing
        mock_fs_output = '{"use_tool": true, "tool": "filesystem", "action": "list_directory", "path": "."}'
        with patch("app.core.planner.planner.process_message", return_value=mock_fs_output):
            plan = decide_tool("list files in this directory")
            self.assertTrue(plan.get("use_tool"))
            self.assertEqual(plan.get("tool"), "filesystem")
            self.assertEqual(plan.get("action"), "list_directory")

        # 3. Git execution
        mock_git_output = '{"use_tool": true, "tool": "git", "action": "run_git", "command": "status"}'
        with patch("app.core.planner.planner.process_message", return_value=mock_git_output):
            plan = decide_tool("run git status")
            self.assertTrue(plan.get("use_tool"))
            self.assertEqual(plan.get("tool"), "git")
            self.assertEqual(plan.get("action"), "run_git")

    # -------------------------------------------------------------------------
    # 6. End-to-End Chat Routing Integration
    # -------------------------------------------------------------------------
    def test_08_e2e_knowledge_question_generates_conversational_response(self):
        # Verify that asking "who is the prime of india" bypasses tool loop and calls process_message
        with patch("app.services.ai_service.process_message", return_value="The Prime Minister of India is Narendra Modi.") as mock_ai:
            reply = generate_response("who is the prime of india")
            self.assertEqual(reply, "The Prime Minister of India is Narendra Modi.")
            mock_ai.assert_called_once()

    def test_09_e2e_question_about_tool_generates_conversational_response(self):
        # Verify that asking "What does git status mean?" calls process_message
        with patch("app.services.ai_service.process_message", return_value="git status displays the state of the working directory and staging area.") as mock_ai:
            reply = generate_response("What does git status mean?")
            self.assertEqual(reply, "git status displays the state of the working directory and staging area.")
            mock_ai.assert_called_once()


if __name__ == "__main__":
    unittest.main()
