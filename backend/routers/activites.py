"""CRUD — Pilier Activités."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/activites", tags=["activites"])


@router.get("", response_model=list[schemas.ActiviteRead])
def list_activites(
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(models.Activite)
    if not include_archived:
        q = q.filter(models.Activite.archived.is_(False))
    return q.order_by(models.Activite.created_at.desc()).all()


@router.post(
    "",
    response_model=schemas.ActiviteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_activite(payload: schemas.ActiviteCreate, db: Session = Depends(get_db)):
    item = models.Activite(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.ActiviteRead)
def get_activite(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Activite, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    return item


@router.patch("/{item_id}", response_model=schemas.ActiviteRead)
def update_activite(
    item_id: int,
    payload: schemas.ActiviteUpdate,
    db: Session = Depends(get_db),
):
    item = db.get(models.Activite, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activite(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Activite, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    item.archived = True
    db.commit()
    return None
