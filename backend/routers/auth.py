"""Authentification — register, login, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _sync_display_name(user: models.User) -> None:
    """Nom affiché = prénom + nom si renseignés."""
    parts = [user.first_name or "", user.last_name or ""]
    full = " ".join(p.strip() for p in parts if p.strip())
    if full:
        user.display_name = full


def _apply_user_update(user: models.User, payload: schemas.UserUpdate) -> None:
    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for key, value in data.items():
        if key == "birth_date":
            if not value:
                value = None
            elif len(value) != 10 or value[4] != "-" or value[7] != "-":
                raise HTTPException(status_code=422, detail="Date de naissance invalide (AAAA-MM-JJ)")
        setattr(user, key, value)
    if password is not None:
        user.hashed_password = auth.hash_password(password)
    if "display_name" not in data:
        _sync_display_name(user)


@router.post(
    "/register",
    response_model=schemas.TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Créer un compte et obtenir un token JWT."""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte avec cet email existe déjà",
        )
    user = models.User(
        email=payload.email,
        hashed_password=auth.hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        display_name=payload.display_name or payload.email.split("@")[0],
    )
    _sync_display_name(user)
    if not user.display_name:
        user.display_name = payload.email.split("@")[0]
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_access_token({"sub": user.id})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserRead.model_validate(user),
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login OAuth2 (username = email)."""
    user = db.query(models.User).filter(models.User.email == form.username).first()
    if user is None or not auth.verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.create_access_token({"sub": user.id})
    return schemas.TokenResponse(
        access_token=token,
        user=schemas.UserRead.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserRead)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Profil de l'utilisateur connecté."""
    return current_user


@router.patch("/me", response_model=schemas.UserRead)
def update_me(
    payload: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Modifier le profil (identité, date de naissance, mot de passe)."""
    _apply_user_update(current_user, payload)
    db.commit()
    db.refresh(current_user)
    return current_user
