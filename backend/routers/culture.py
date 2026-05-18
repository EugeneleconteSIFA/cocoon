"""CRUD — Pilier Culture (films & séries)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/culture", tags=["culture"])


@router.get("", response_model=list[schemas.CultureRead])
def list_culture(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    q = db.query(models.Culture).filter(models.Culture.cocon_id == current_cocon.id)
    if not include_archived:
        q = q.filter(models.Culture.archived.is_(False))
    return q.order_by(models.Culture.created_at.desc()).all()


@router.post(
    "",
    response_model=schemas.CultureRead,
    status_code=status.HTTP_201_CREATED,
)
def create_culture(
    payload: schemas.CultureCreate,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    data = payload.model_dump()
    data["cocon_id"] = current_cocon.id
    item = models.Culture(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.CultureRead)
def get_culture(
    item_id: int,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    item = db.get(models.Culture, item_id)
    if item is None or item.cocon_id != current_cocon.id:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    return item


@router.patch("/{item_id}", response_model=schemas.CultureRead)
def update_culture(
    item_id: int,
    payload: schemas.CultureUpdate,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    item = db.get(models.Culture, item_id)
    if item is None or item.cocon_id != current_cocon.id:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_culture(
    item_id: int,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    """Soft delete : passe `archived=True`. Pas de hard delete en V1."""
    item = db.get(models.Culture, item_id)
    if item is None or item.cocon_id != current_cocon.id:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    item.archived = True
    db.commit()
    return None
