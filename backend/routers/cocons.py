"""Gestion des Cocons (espaces partagés à deux)."""

from __future__ import annotations

import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/cocons", tags=["cocons"])


def _generate_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def _cocon_read(cocon: models.Cocon, role: str, db: Session) -> schemas.CoconRead:
    member_count = (
        db.query(models.CoconMember)
        .filter(models.CoconMember.cocon_id == cocon.id)
        .count()
    )
    return schemas.CoconRead(
        id=cocon.id,
        name=cocon.name,
        code=cocon.code,
        role=role,
        member_count=member_count,
        created_at=cocon.created_at,
    )


@router.post("", response_model=schemas.CoconRead, status_code=status.HTTP_201_CREATED)
def create_cocon(
    payload: schemas.CoconCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Créer un nouveau Cocon et en devenir propriétaire."""
    # Générer un code unique
    code = _generate_code()
    while db.query(models.Cocon).filter(models.Cocon.code == code).first():
        code = _generate_code()

    cocon = models.Cocon(
        name=payload.name,
        code=code,
        created_by=current_user.id,
    )
    db.add(cocon)
    db.flush()  # pour obtenir l'id avant le commit

    membership = models.CoconMember(
        cocon_id=cocon.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(membership)
    db.commit()
    db.refresh(cocon)

    return _cocon_read(cocon, role="owner", db=db)


@router.post("/join", response_model=schemas.CoconRead)
def join_cocon(
    payload: schemas.CoconJoin,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Rejoindre un Cocon existant via son code d'invitation."""
    cocon = db.query(models.Cocon).filter(models.Cocon.code == payload.code).first()
    if cocon is None:
        raise HTTPException(status_code=404, detail="Code invalide ou Cocon introuvable")

    already_member = (
        db.query(models.CoconMember)
        .filter(
            models.CoconMember.cocon_id == cocon.id,
            models.CoconMember.user_id == current_user.id,
        )
        .first()
    )
    if already_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vous êtes déjà membre de ce Cocon",
        )

    membership = models.CoconMember(
        cocon_id=cocon.id,
        user_id=current_user.id,
        role="member",
    )
    db.add(membership)
    db.commit()

    return _cocon_read(cocon, role="member", db=db)


@router.get("", response_model=list[schemas.CoconRead])
def list_cocons(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Liste des Cocons dont je suis membre."""
    memberships = (
        db.query(models.CoconMember)
        .filter(models.CoconMember.user_id == current_user.id)
        .all()
    )
    result = []
    for m in memberships:
        cocon = db.get(models.Cocon, m.cocon_id)
        if cocon:
            result.append(_cocon_read(cocon, role=m.role, db=db))
    return result
