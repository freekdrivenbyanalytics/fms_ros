from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

SESSION_COOKIE_NAME = "session"
_JWT_ALGORITHM = "HS256"
_SESSION_TTL = timedelta(days=7)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_session_token(user: User) -> str:
    payload = {
        "user_id": user.id,
        "is_admin": user.is_admin,
        "exp": datetime.now(timezone.utc) + _SESSION_TTL,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=_JWT_ALGORITHM)


def decode_session_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[_JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        return None

    payload = decode_session_token(token)
    if payload is None:
        return None

    user = db.get(User, payload["user_id"])
    if user is None or user.delete_flag:
        return None
    return user


def require_admin(user: User | None = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_customer_access(
    customer_id: int,
    user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    if user.is_admin:
        return user
    assigned_ids = {customer.id for customer in user.customers}
    if customer_id not in assigned_ids:
        raise HTTPException(status_code=403, detail="Customer access required")
    return user


def require_session(user: User | None = Depends(get_current_user)) -> User:
    """Any logged-in user, admin or customer — for Customer Portal endpoints
    that aren't scoped by a single customer_id path param (list endpoints),
    where per-row scoping is applied separately via customer_scope_ids."""
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


def customer_scope_ids(user: User) -> list[int] | None:
    """None means unrestricted (admin); otherwise the exact set of customer
    ids a customer session may see."""
    if user.is_admin:
        return None
    return [customer.id for customer in user.customers]
