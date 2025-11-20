import os
import tempfile

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base, get_db
from src.main import app

# Setup a temporary SQLite database for this manual test
fd, db_path = tempfile.mkstemp()
os.close(fd)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Override get_db dependency for the TestClient
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def run_manual_test():
    print("--- Starting Manual Test ---")

    # Test 0: Login to get an access token
    print("POST /api/v1/token with username and password")
    login_data = {"username": "testuser", "password": "testpassword"}
    token_response = client.post("/api/v1/token", data=login_data)
    print(f"Token Response Status Code: {token_response.status_code}")
    print(f"Token Response JSON: {token_response.json()}")
    assert token_response.status_code == status.HTTP_200_OK
    access_token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Test 1: Create a repository analysis request
    repo_url = "https://github.com/octocat/Spoon-Knife"
    print(f"POST /api/v1/repositories/ with url: {repo_url}")
    post_response = client.post("/api/v1/repositories/", json={"url": repo_url}, headers=headers)
    print(f"POST Response Status Code: {post_response.status_code}")
    print(f"POST Response JSON: {post_response.json()}")
    assert post_response.status_code == status.HTTP_201_CREATED
    repo_data = post_response.json()
    repo_id = repo_data["id"]
    print(f"Created Repository ID: {repo_id}")

    # Test 2: Retrieve analysis results for the repository
    print(f"GET /api/v1/repositories/{repo_id}/analysis")
    get_response = client.get(f"/api/v1/repositories/{repo_id}/analysis", headers=headers)
    print(f"GET Response Status Code: {get_response.status_code}")
    print(f"GET Response JSON: {get_response.json()}")

    # Clean up the temporary database file
    os.unlink(db_path)

if __name__ == "__main__":
    run_manual_test()
