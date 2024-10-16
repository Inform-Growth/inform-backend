import os
import sys
from pathlib import Path
# Add the project root to the Python path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from main import app
# from main11 import app # Adjusted import after modifying the path
from unittest.mock import patch

# client = TestClient(app)
client = TestClient(app)

def test_handle_initial_submission():
    form_id = "665a369ee79487753920153a"
    initial_submission = {
        "email": "jar.sand.on@gmail.com",
        "occupation": "Test",
        "initial-thoughts": "I like the colours but the style could be friendlier. Rounded corners are nice"
    }
    # with patch('app.services.submission_service.SubmissionService.handle_initial_submission') as mock_handle_initial:
    #     mock_handle_initial.return_value = {
    #         "submission_id": "mocked_submission_id",
    #         "question": "What do you think about the navigation?",
    #         "suggestions": ["It's intuitive", "It's confusing"]
    #     }
    response = client.post("/api/v1/submission/", json={"form_id": form_id, "context": initial_submission})
    assert response.status_code == 200
    print(response.json())

# def test_handle_submission_response():
#     submission_id = "mocked_submission_id"
#     user_response = "It's intuitive"
#     response = client.post(f"/api/v1/submission/{submission_id}", json={"response": user_response})
#     assert response.status_code == 200

# # Example of additional test cases
# def test_submission_endpoint_not_found():
#     response = client.post("/api/v1/nonexistent_endpoint", json={})
#     assert response.status_code == 404

# def test_handle_initial_submission_with_invalid_data():
#     form_id = "invalid_form_id"
#     initial_submission = {}  # Sending empty data to simulate invalid submission
#     with patch('app.services.submission_service.SubmissionService.handle_initial_submission') as mock_handle_initial:
#         mock_handle_initial.return_value = None  # Assuming the service returns None for invalid submissions
#         response = client.post("/api/v1/submission/", json={"form_id": form_id, "context": initial_submission})
#         assert response.status_code != 200  # Expecting a status code indicating failure (e.g., 400 Bad Request)