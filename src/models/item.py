from typing import Optional
from sqlmodel import SQLModel, Field


class ItemDB(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)


class ItemBase(SQLModel):
    name: str
    price: float
    is_offer: Optional[bool] = None


class Item(ItemBase, ItemDB, table=True):
    pass


class ItemCreate(ItemBase):
    pass


class ItemId(SQLModel):
    id: int


class ItemRead(ItemBase, ItemId):
    pass
