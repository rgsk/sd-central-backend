from fastapi import APIRouter
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


# In-memory storage for items
items_db: dict[int, Item] = {}
next_item_id = 1


# CRUD APIs for Items
@router.post("")
def create_item(item: Item):
    """Create a new item"""
    global next_item_id
    item_id = next_item_id
    next_item_id += 1
    items_db[item_id] = item
    return {"id": item_id, **item.model_dump()}


@router.get("")
def list_items():
    """Get all items"""
    return {
        "items": [{"id": item_id, **item.model_dump()} for item_id, item in items_db.items()]
    }


@router.get("/{item_id}")
def get_item(item_id: int):
    """Get a specific item by ID"""
    if item_id in items_db:
        return {"id": item_id, **items_db[item_id].model_dump()}
    return {"error": "Item not found"}


@router.put("/{item_id}")
def update_item(item_id: int, item: Item):
    """Update an item"""
    if item_id in items_db:
        items_db[item_id] = item
        return {"id": item_id, **item.model_dump()}
    return {"error": "Item not found"}


@router.delete("/{item_id}")
def delete_item(item_id: int):
    """Delete an item"""
    if item_id in items_db:
        deleted_item = items_db.pop(item_id)
        return {"message": "Item deleted", 'item': {"id": item_id, **deleted_item.model_dump()}}
    return {"error": "Item not found"}
