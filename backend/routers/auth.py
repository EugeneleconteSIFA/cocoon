"""Authentification — register, login, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


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
        display_name=payload.display_name or payload.email.split('@')[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = auth.create_access_token({"sub": str(user.id)})
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
    token = auth.create_access_token({"sub": str(user.id)})
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
    """Modifier le profil (display_name et/ou password)."""
    if payload.display_name is not None:
        current_user.display_name = payload.display_name
    if payload.password is not None:
        current_user.hashed_password = auth.hash_password(payload.password)
    db.commit()
    db.refresh(current_user)
    return current_user
