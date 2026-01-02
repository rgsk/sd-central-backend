from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ItemDB(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ItemBase(SQLModel):
    name: str
    price: float
    is_offer: Optional[bool] = None


class Item(ItemBase, ItemDB, table=True):
    pass


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    name: Optional[str] = None
    price: Optional[float] = None
    is_offer: Optional[bool] = None


class ItemId(SQLModel):
    id: int


class ItemRead(ItemBase, ItemId):
    created_at: datetime
