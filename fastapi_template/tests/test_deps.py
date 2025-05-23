from fastapi import HTTPException
from jose import jwt
from app.api.deps import get_current_user, get_current_active_user, get_current_active_superuser
from app.core import security
from app.models import User


def test_get_current_user(db, client):
    # Create a test user
    user_data = {"email": "test@example.com", "password": "testpassword"}
    user = User(**user_data)
    db.add(user)
    db.commit()

    # Generate a token for the user
    token = security.create_access_token(data={"id": str(user.id), "email": user.email})

    # Test get_current_user
    current_user = get_current_user(db=db, token=token)
    assert current_user.email == user.email


def test_get_current_active_user(db, client):
    # Create a test user
    user_data = {"email": "test@example.com", "password": "testpassword", "is_active": True}
    user = User(**user_data)
    db.add(user)
    db.commit()

    # Generate a token for the user
    token = security.create_access_token(data={"id": str(user.id), "email": user.email})

    # Test get_current_active_user
    current_user = get_current_active_user(current_user=user)
    assert current_user.is_active


def test_get_current_active_superuser(db, client):
    # Create a test superuser
    user_data = {"email": "admin@example.com", "password": "adminpassword", "is_superuser": True}
    user = User(**user_data)
    db.add(user)
    db.commit()

    # Test get_current_active_superuser
    current_user = get_current_active_superuser(current_user=user)
    assert current_user.is_superuser
