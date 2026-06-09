"""Shared FastAPI dependencies: authentication and role checks.

Supports two token sources:
  * Authorization: Bearer <token> header (API clients / Swagger)
  * access_token cookie (server-rendered HTML pages)
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _extract_token(request: Request, bearer: Optional[str]) -> Optional[str]:
    if bearer:
        return bearer
    cookie_token = request.cookies.get("access_token")
    if cookie_token and cookie_token.startswith("Bearer "):
        return cookie_token[len("Bearer "):]
    return cookie_token


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    raw_token = _extract_token(request, token)
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учётные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not raw_token:
        raise credentials_exc

    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        raise credentials_exc

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise credentials_exc
    return user


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None instead of raising.

    Used by HTML pages that adapt their UI to anonymous users.
    """
    raw_token = _extract_token(request, None)
    if not raw_token:
        return None
    payload = decode_access_token(raw_token)
    if not payload or "sub" not in payload:
        return None
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        return None
    return user


def require_roles(*roles: UserRole):
    """Dependency factory enforcing that the current user has one of roles."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для выполнения операции",
            )
        return current_user

    return checker
