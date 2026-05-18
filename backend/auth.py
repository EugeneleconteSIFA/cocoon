from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from . import models
from .database import get_db

log = logging.getLogger(__name__)

SECRET_KEY = (os.getenv("SECRET_KEY") or "").strip()
if not SECRET_KEY:
    import secrets as _s
    SECRET_KEY = _s.token_hex(32)
    if os.getenv("APP_ENV", "local").strip() == "production":
        log.error(
            "SECRET_KEY absente en production — les JWT sont invalidés à chaque redémarrage. "
            "Ajoute SECRET_KEY dans backend/.env"
        )
    else:
        log.warning("SECRET_KEY non définie — clé aléatoire (dev uniquement)")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session invalide ou expirée",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise exc
        user_id = int(sub)
    except (JWTError, TypeError, ValueError):
        raise exc
    user = db.get(models.User, user_id)
    if user is None:
        raise exc
    return user


def get_active_cocon(
    x_cocon_id: int | None = Header(default=None, alias="X-Cocon-Id"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.Cocon:
    if x_cocon_id is None:
        raise HTTPException(status_code=400, detail="X-Cocon-Id manquant")
    membership = (
        db.query(models.CoconMember)
        .filter(
            models.CoconMember.cocon_id == x_cocon_id,
            models.CoconMember.user_id == current_user.id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Pas membre de ce cocon")
    cocon = db.get(models.Cocon, x_cocon_id)
    if cocon is None:
        raise HTTPException(status_code=404, detail="Cocon introuvable")
    return cocon
