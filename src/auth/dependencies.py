# src/auth/dependencies.py
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from src.database import get_session
from src.models.user import Usuario
from src.auth.security import decode_username

# Apunta al endpoint exacto donde el cliente obtiene el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

COOKIE_NAME = "access_token"


def _get_user(session: Session, username: str) -> Optional[Usuario]:
    return session.exec(select(Usuario).where(Usuario.username == username)).first()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = decode_username(token)
    if username is None:
        raise credentials_exception
    usuario = _get_user(session, username)
    if usuario is None:
        raise credentials_exception
    return usuario


def get_optional_user_from_cookie(
    request: Request,
    session: Session = Depends(get_session),
) -> Optional[Usuario]:
    """Para las vistas Jinja2: el JWT viaja en una cookie HttpOnly."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    username = decode_username(token)
    if username is None:
        return None
    return _get_user(session, username)
