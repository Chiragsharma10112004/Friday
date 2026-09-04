"""
Live integration verification script testing real API endpoints and end-to-end chat/memory workflows.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi.testclient import TestClient
from app.main import app
from app.memory.database import SessionLocal
from app.application_pipeline.models import TrackedApplication

def run_live_verification():
    print("==================================================", flush=True)
    print("STARTING LIVE INTEGRATION VERIFICATION", flush=True)
    print("==================================================", flush=True)

    client = TestClient(app)

    # 1. Send chat message
    print("\n[Step 1] Sending chat message: 'Hello FRIDAY, this is a live test!'...")
    res1 = client.post("/chat", json={"message": "Hello FRIDAY, this is a live test!"})
    print(f"Status Code: {res1.status_code}")
    print(f"Response: {res1.json()}")
    assert res1.status_code == 200, f"Expected 200, got {res1.status_code}"
    assert "reply" in res1.json()

    # 2. Check history persistence
    print("\n[Step 2] Checking /memory/history endpoint for conversation persistence...")
    res2 = client.get("/memory/history?limit=10")
    print(f"Status Code: {res2.status_code}")
    history = res2.json()
    print(f"Total history entries: {len(history)}")
    for idx, item in enumerate(history[-4:]):
        print(f"  [{idx}] {item['role'].upper()}: {item['content'][:80]}...")
    assert res2.status_code == 200
    assert len(history) >= 2
    assert any(m["role"] == "user" and "Hello FRIDAY" in m["content"] for m in history)
    assert any(m["role"] == "assistant" for m in history)

    # 3. Store memory
    print("\n[Step 3] Storing fact: favorite_language = 'Python'...")
    res3 = client.post("/memory", json={"key": "favorite_language", "value": "Python"})
    print(f"Status Code: {res3.status_code}, Response: {res3.json()}")
    assert res3.status_code == 200

    # 4. Ask about favorite programming language
    print("\n[Step 4] Asking: 'What is my favorite programming language?'...")
    res4 = client.post("/chat", json={"message": "What is my favorite programming language?"})
    print(f"Status Code: {res4.status_code}")
    print(f"Assistant Reply: {res4.json().get('reply')}")
    assert res4.status_code == 200
    reply4 = res4.json().get("reply", "")
    assert "Python" in reply4, f"Expected 'Python' in reply, got: {reply4}"

    # 5. Create a tracked application and ask for health summary
    print("\n[Step 5] Adding an active application to test pipeline context...")
    db = SessionLocal()
    try:
        app_record = db.query(TrackedApplication).filter(TrackedApplication.company == "Stripe").first()
        if not app_record:
            app_record = TrackedApplication(
                company="Stripe",
                role="Staff Infrastructure Engineer",
                status="TECHNICAL",
                priority="HIGH",
                match_score=0.92
            )
            db.add(app_record)
            db.commit()
    finally:
        db.close()

    print("\n[Step 6] Asking: 'Summarize the health status of my active job applications.'...")
    res5 = client.post("/chat", json={"message": "Summarize the health status of my active job applications."})
    print(f"Status Code: {res5.status_code}")
    print(f"Assistant Reply:\n{res5.json().get('reply')}")
    assert res5.status_code == 200
    reply5 = res5.json().get("reply", "")
    assert ("Stripe" in reply5 or "Health" in reply5 or "Application" in reply5), f"Expected application context in reply, got: {reply5}"

    # 6. Test normal conversational query
    print("\n[Step 7] Asking normal conversational question: 'How is everything running today?'...")
    res6 = client.post("/chat", json={"message": "How is everything running today?"})
    print(f"Status Code: {res6.status_code}")
    print(f"Assistant Reply: {res6.json().get('reply')}")
    assert res6.status_code == 200
    reply6 = res6.json().get("reply", "")
    assert "Tool execution failed" not in reply6

    print("\n==================================================")
    print("ALL LIVE INTEGRATION CHECKS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_live_verification()
