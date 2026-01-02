from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from db import get_session
from models.item import Item, ItemCreate, ItemListResponse, ItemRead, ItemUpdate

router = APIRouter(
    prefix="/items",
    tags=["items"]
)


@router.post("", response_model=ItemRead)
def create_item(item: ItemCreate, session: Session = Depends(get_session)):
    db_item = Item(**item.model_dump())
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.get("", response_model=ItemListResponse)
def list_items(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    total = session.exec(select(func.count()).select_from(Item)).one()
    statement = (
        select(Item)
        .order_by(col(Item.created_at))
        .offset(offset)
        .limit(limit)
    )
    items = cast(list[ItemRead], session.exec(statement).all())
    return ItemListResponse(total=total, items=items)


@router.get("/{item_id}", response_model=ItemRead)
def get_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/{item_id}", response_model=ItemRead)
def partial_update_item(
    item_id: int,
    item: ItemUpdate,
    session: Session = Depends(get_session),
):
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_item, key, value)

    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    db_item = session.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(db_item)
    session.commit()
    return {"message": "Item deleted"}
