from fastapi import status
from app.models import User


def test_login_access_token(client, db):
    # Create a test user
    user_data = {"email": "test@example.com", "password": "testpassword"}
    user = User(**user_data)
    db.add(user)
    db.commit()

    # Test login with correct credentials
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": user.email, "password": user_data["password"]},
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()

    # Test login with incorrect credentials
    response = client.post(
        "/api/v1/login/access-token",
        data={"username": user.email, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
