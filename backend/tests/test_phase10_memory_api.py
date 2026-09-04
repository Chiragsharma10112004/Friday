"""
Unit & Integration Tests for Phase 10 Memory API, Context Retrieval & Chat Persistence.
"""
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.memory.database import SessionLocal, Base, engine
from app.memory.models import UserMemory, ChatHistory
from app.memory.repository import save_memory, get_memory, delete_memory, get_all_memory, get_recent_messages, save_message
from app.memory.memory_manager import build_memory_context, process_memory, _extract_facts_rule_based
from app.profile.models import UserProfile


class Phase10MemoryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        db = SessionLocal()
        try:
            # Ensure standard master profile is restored for other test suites
            profile = db.query(UserProfile).first()
            if not profile:
                profile = UserProfile(
                    first_name="Chirag",
                    last_name="Sharma",
                    email="chirag@example.com",
                    phone="+1-555-0199",
                    location="San Francisco, CA",
                    headline="Senior AI Backend Engineer",
                    skills="Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, GenAI, LLMs",
                    target_roles="Senior AI Backend Engineer",
                    work_authorization="Authorized to work in US/India",
                    sponsorship_required="No"
                )
                db.add(profile)
                db.commit()
        finally:
            db.close()

    def setUp(self):
        self.db = SessionLocal()
        self.db.query(UserMemory).delete()
        self.db.query(ChatHistory).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_01_create_retrieve_update_delete_memory_api(self):
        """Test complete CRUD lifecycle through the /memory API endpoints."""
        # 1. Create memory
        res = self.client.post("/memory", json={"key": "favorite_language", "value": "Python"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("key"), "favorite_language")
        self.assertEqual(data.get("value"), "Python")

        # 2. List all memories
        res = self.client.get("/memory")
        self.assertEqual(res.status_code, 200)
        list_data = res.json()
        self.assertIn("memories", list_data)
        self.assertIn("favorite_language", list_data["memories"])
        self.assertEqual(list_data["memories"]["favorite_language"], "Python")
        self.assertEqual(list_data["total_count"], 1)

        # 3. Retrieve single memory key
        res = self.client.get("/memory/favorite_language")
        self.assertEqual(res.status_code, 200)
        single_data = res.json()
        self.assertEqual(single_data.get("key"), "favorite_language")
        self.assertEqual(single_data.get("value"), "Python")

        # 4. Update memory key
        res = self.client.post("/memory", json={"key": "favorite_language", "value": "Python & TypeScript"})
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/memory/favorite_language")
        self.assertEqual(res.json().get("value"), "Python & TypeScript")

        # 5. Delete memory key
        res = self.client.delete("/memory/favorite_language")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))

        # 6. Verify 404 on deleted / non-existent key
        res = self.client.get("/memory/favorite_language")
        self.assertEqual(res.status_code, 404)

        res = self.client.delete("/memory/non_existent_key_999")
        self.assertEqual(res.status_code, 404)

        # 7. Invalid empty key validation
        res = self.client.post("/memory", json={"key": "  ", "value": "test"})
        self.assertEqual(res.status_code, 400)

    def test_02_chat_persistence_and_history_retrieval(self):
        """Test that /chat saves both user and assistant turns to /memory/history."""
        # Send a chat message
        res = self.client.post("/chat", json={"message": "Hello FRIDAY, can you hear me?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("reply", data)
        self.assertTrue(len(data["reply"]) > 0)

        # Retrieve history from /memory/history
        res = self.client.get("/memory/history?limit=10")
        self.assertEqual(res.status_code, 200)
        history = res.json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 2)

        # User message should be first, followed by assistant reply
        roles = [msg["role"] for msg in history]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)

        # Check content of user message
        user_msgs = [m["content"] for m in history if m["role"] == "user"]
        self.assertIn("Hello FRIDAY, can you hear me?", user_msgs)

    def test_03_memory_extraction_and_learning_flow(self):
        """Test deterministic fact extraction and context usage."""
        # 1. Test rule-based fact extraction helper
        facts = _extract_facts_rule_based("My favorite programming language is Python.")
        self.assertEqual(facts.get("favorite_language"), "Python")

        facts_name = _extract_facts_rule_based("My name is Alice Smith")
        self.assertEqual(facts_name.get("name"), "Alice Smith")

        facts_email = _extract_facts_rule_based("My email is alice@example.com")
        self.assertEqual(facts_email.get("email"), "alice@example.com")

        # 2. Test process_memory writes to database
        process_memory(self.db, "My favorite programming language is Python.")
        val = get_memory(self.db, "favorite_language")
        self.assertEqual(val, "Python")

        # 3. Context builder should include the learned fact
        ctx = build_memory_context(self.db)
        self.assertIn("favorite_language: Python", ctx)

    def test_04_user_profile_integration_in_memory_context(self):
        """Test that structured UserProfile table is consumed by build_memory_context."""
        # Ensure a user profile exists
        profile = self.db.query(UserProfile).first()
        if not profile:
            profile = UserProfile(
                first_name="Chirag",
                last_name="Sharma",
                email="chirag@example.com",
                location="San Francisco, CA",
                skills="Python, FastAPI, TypeScript, React",
                target_roles="Senior AI Engineer"
            )
            self.db.add(profile)
            self.db.commit()

        # Build context
        ctx = build_memory_context(self.db)
        self.assertIn("Chirag", ctx)
        self.assertIn("chirag@example.com", ctx)

    def test_05_conversational_query_does_not_invoke_application_tools(self):
        """Test that standard greetings/chat queries pass cleanly through conversational pipeline."""
        res = self.client.post("/chat", json={"message": "Good morning! How is the weather in cyberspace?"})
        self.assertEqual(res.status_code, 200)
        reply = res.json().get("reply", "")
        self.assertTrue(len(reply) > 0)
        # Should not mention tool execution failures or errors
        self.assertNotIn("Tool execution failed", reply)


if __name__ == "__main__":
    unittest.main()
