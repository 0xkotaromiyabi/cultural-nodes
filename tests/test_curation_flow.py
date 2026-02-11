# import pytest  <-- Removed
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.main import app
from app.core.knowledge_store import get_knowledge_store

client = TestClient(app)

# Mock headers for different roles
headers_contributor = {
    "X-User-ID": "test_user",
    "X-User-Role": "contributor"
}

headers_curator = {
    "X-User-ID": "test_admin",
    "X-User-Role": "curator"
}

def test_curation_flow():
    # 1. Submit Knowledge (as Contributor)
    print("\n[Test] Submitting Knowledge...")
    payload = {
        "title": "Test Submission",
        "source_type": "community",
        "content": "This is a test content for curation.",
        "category": "test"
    }
    
    response = client.post("/api/curation/submit", json=payload, headers=headers_contributor)
    if response.status_code != 200:
        print(f"FAILED SUBMIT: {response.status_code} - {response.text}")
    assert response.status_code == 200
    data = response.json()
    submission_id = data["id"]
    print(f"   -> Submission ID: {submission_id}")
    assert data["status"] == "pending"
    assert data["submitted_by"] == "test_user"

    # 2. List Submissions (as Curator)
    print("[Test] Listing Submissions...")
    response = client.get("/api/curation/submissions?status=pending", headers=headers_curator)
    assert response.status_code == 200
    submissions = response.json()
    
    found = False
    for sub in submissions:
        if sub["id"] == submission_id:
            found = True
            break
    assert found
    print("   -> Submission found in pending list")

    # 3. Approve Submission (as Curator)
    print(f"[Test] Approving Submission {submission_id}...")
    
    # Mock the background task ingestion to avoid actual processing overhead in test
    with patch("app.api.curation.process_ingestion") as mock_ingest:
        action_payload = {"note": "Looks good"}
        response = client.post(
            f"/api/curation/submissions/{submission_id}/approve", 
            json=action_payload, 
            headers=headers_curator
        )
        assert response.status_code == 200
        assert response.json()["status"] == "approved"
        
        # Verify mocked ingestion was called
        mock_ingest.assert_called_once()
        print("   -> Approved and Ingestion triggered")

    # 4. Verify Status Updated
    # We can check directly via store or listing again
    store = get_knowledge_store()
    updated_sub = store.get_submission_by_id(submission_id)
    assert updated_sub["status"] == "approved"
    assert updated_sub["curator_id"] == "test_admin"

    print("[Test] Flow Complete: Submit -> List -> Approve -> Verified")

if __name__ == "__main__":
    # Manually run if executed directly
    try:
        test_curation_flow()
        print("\n✅ ALL TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
