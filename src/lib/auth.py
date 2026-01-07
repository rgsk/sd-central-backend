from fastapi import Depends, Header, HTTPException, Request
from firebase_admin import auth
from firebase_admin._auth_utils import InvalidIdTokenError
from sqlmodel import Session, select

from db import get_session
from lib.firebase_admin import get_firebase_app
from models.user import User


def get_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Invalid Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if not token or token == "undefined":
        raise HTTPException(status_code=401, detail="Missing token")
    return token


def get_decoded_token(token: str):
    try:
        get_firebase_app()
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_user(
    request: Request,
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    token = get_bearer_token(authorization)
    decoded_token = get_decoded_token(token)
    email = decoded_token.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Email not found in token")
    user = session.exec(
        select(User).where(User.email == email)
    ).one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    request.state.current_user = user
    request.state.decoded_token = decoded_token
    return user
