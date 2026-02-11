from fastapi.testclient import TestClient
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.main import app

client = TestClient(app)

def test_login():
    print("\n[Test] Testing Login Endpoint...")
    
    # 1. Valid Login
    payload = {"username": "admin", "password": "admin123"}
    response = client.post("/api/auth/login", json=payload)
    
    if response.status_code == 200:
        print("✅ Valid login successful")
        data = response.json()
        assert data["user_id"] == "admin"
        assert data["role"] == "curator"
        assert "token" in data
    else:
        print(f"❌ Valid login failed: {response.text}")

    # 2. Invalid Login
    payload_bad = {"username": "admin", "password": "wrongpassword"}
    response = client.post("/api/auth/login", json=payload_bad)
    
    if response.status_code == 401:
        print("✅ Invalid login rejected (401)")
    else:
        print(f"❌ Invalid login not rejected correctly: {response.status_code}")

if __name__ == "__main__":
    test_login()
