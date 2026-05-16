"""CRUD — Pilier Lieux (ville, autres villes, voyages)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/lieux", tags=["lieux"])


@router.get("", response_model=list[schemas.LieuRead])
def list_lieux(
    include_archived: bool = False,
    section: str | None = Query(default=None, pattern="^(ville|autre_ville|voyage)$"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Lieu)
    if not include_archived:
        q = q.filter(models.Lieu.archived.is_(False))
    if section is not None:
        q = q.filter(models.Lieu.section == section)
    return q.order_by(models.Lieu.created_at.desc()).all()


@router.post(
    "",
    response_model=schemas.LieuRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lieu(payload: schemas.LieuCreate, db: Session = Depends(get_db)):
    item = models.Lieu(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.LieuRead)
def get_lieu(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Lieu, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    return item


@router.patch("/{item_id}", response_model=schemas.LieuRead)
def update_lieu(
    item_id: int,
    payload: schemas.LieuUpdate,
    db: Session = Depends(get_db),
):
    item = db.get(models.Lieu, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lieu(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.Lieu, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    item.archived = True
    db.commit()
    return None
