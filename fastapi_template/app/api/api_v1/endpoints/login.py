from datetime import timedelta, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.utils import (
    generate_password_reset_token,
    send_reset_password_email,
    verify_password_reset_token,
)

router = APIRouter()


@router.post("/access-token", response_model=schemas.Token)
def login_access_token(
        db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    token = security.create_access_token(
        data={"id": str(user.id), "email": form_data.username},
        expires_delta=access_token_expires,
    )
    token_data = deps.get_user(token)
    user = crud.user.get(db=db, id=token_data.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"access_token": token, "token_type": "Bearer"}


@router.post("/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    expired_date = datetime(year=2025, month=8, day=31)
    current_date = datetime.now()
    if current_date >= expired_date:
        raise HTTPException(status_code=400, detail="Expired Version")
    return current_user


@router.post("/test-token/{token}", response_model=schemas.User)
def test_token(token: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Test access token
    """
    token_data = deps.get_user(token)
    user = crud.user.get(db=db, uuid=token_data.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/decode_token", response_model=schemas.TokenPayload)
def test_token(token_info=Depends(deps.get_token_info)) -> Any:
    """
    Test access token
    """
    return token_info


@router.post("/password-recovery/", response_model=schemas.Msg)
def recover_password(email: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud.user.get_by_email(db, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password/", response_model=schemas.Msg)
def reset_password(
        token: str = Body(...),
        new_password: str = Body(...),
        db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.user.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    return {"msg": "Password updated successfully"}
