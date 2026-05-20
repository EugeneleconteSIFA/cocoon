"""CRUD — Pilier Cuisine (recettes)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/cuisine", tags=["cuisine"])


@router.get("", response_model=list[schemas.RecetteRead])
def list_cuisine(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    q = db.query(models.Recette).filter(models.Recette.cocon_id == current_cocon.id)
    if not include_archived:
        q = q.filter(models.Recette.archived.is_(False))
    return q.order_by(models.Recette.created_at.desc()).all()


@router.post(
    "",
    response_model=schemas.RecetteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_recette(
    payload: schemas.RecetteCreate,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    data = payload.model_dump()
    data["cocon_id"] = current_cocon.id
    item = models.Recette(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.RecetteRead)
def get_recette(
    item_id: int,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    item = db.get(models.Recette, item_id)
    if item is None or item.cocon_id != current_cocon.id:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    return item


@router.patch("/{item_id}", response_model=schemas.RecetteRead)
def update_recette(
    item_id: int,
    payload: schemas.RecetteUpdate,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    item = db.get(models.Recette, item_id)
    if item is None or item.cocon_id != current_cocon.id:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recette(
    item_id: int,
    db: Session = Depends(get_db),
    current_cocon: models.Cocon = Depends(auth.get_active_cocon),
):
    item = db.get(models.Recette, item_id)
    if item is None or item.cocon_id != current_cocon.id:
        raise HTTPException(status_code=404, detail="Pas trouvé")
    item.archived = True
    db.commit()
    return None
