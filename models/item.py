from typing import Optional
from sqlmodel import SQLModel, Field


class ItemBase(SQLModel):
    name: str
    price: float
    is_offer: Optional[bool] = None


class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: int
