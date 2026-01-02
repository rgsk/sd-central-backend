from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class AppSettingsDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
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
    default_academic_term_id: Optional[UUID] = Field(
        default=None,
        foreign_key="academic_terms.id",
        sa_type=PG_UUID(as_uuid=True),
    )


class AppSettings(AppSettingsBase, AppSettingsDB, table=True):
    __tablename__ = "app_settings"  # type: ignore
    pass


class AppSettingsUpdate(SQLModel):
    default_academic_term_id: Optional[UUID] = None


class AppSettingsId(SQLModel):
    id: UUID


class AppSettingsRead(AppSettingsBase, AppSettingsId):
    created_at: datetime
    updated_at: datetime
