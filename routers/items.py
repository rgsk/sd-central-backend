from fastapi import APIRouter, HTTPException
from typing import Union

from pydantic import BaseModel

router = APIRouter(
    prefix="/items",
    tags=["items"]
)


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    is_offer: Union[bool, None] = None


class ItemListResponse(BaseModel):
    items: list[ItemResponse]


class MessageResponse(BaseModel):
    message: str


# In-memory storage for items
items_db: dict[int, Item] = {}
next_item_id = 1


# CRUD APIs for Items
@router.post("", response_model=ItemResponse)
def create_item(item: Item):
    """Create a new item"""
    global next_item_id
    item_id = next_item_id
    next_item_id += 1
    items_db[item_id] = item
    return {"id": item_id, **item.model_dump()}


@router.get("", response_model=ItemListResponse)
def list_items():
    """Get all items"""
    return {
        "items": [{"id": item_id, **item.model_dump()} for item_id, item in items_db.items()]
    }


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int):
    """Get a specific item by ID"""
    if item_id in items_db:
        return {"id": item_id, **items_db[item_id].model_dump()}
    raise HTTPException(status_code=404, detail="Item not found")


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: Item):
    """Update an item"""
    if item_id in items_db:
        items_db[item_id] = item
        return {"id": item_id, **item.model_dump()}
    raise HTTPException(status_code=404, detail="Item not found")


@router.delete("/{item_id}", response_model=MessageResponse)
def delete_item(item_id: int):
    """Delete an item"""
    if item_id in items_db:
        items_db.pop(item_id)
        return {"message": "Item deleted"}
    raise HTTPException(status_code=404, detail="Item not found")
