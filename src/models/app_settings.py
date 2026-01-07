from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


SINGLETON_APP_SETTINGS_ID = UUID("00000000-0000-0000-0000-000000000001")


class AppSettingsDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=lambda: SINGLETON_APP_SETTINGS_ID,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AppSettingsBase(SQLModel):
    test_field: str = ""


class AppSettings(AppSettingsBase, AppSettingsDB, table=True):
    __tablename__ = "app_settings"  # type: ignore
    pass


class AppSettingsUpdate(SQLModel):
    test_field: Optional[str] = None


class AppSettingsId(SQLModel):
    id: UUID


class AppSettingsRead(AppSettingsBase, AppSettingsId):
    created_at: datetime
    updated_at: datetime
