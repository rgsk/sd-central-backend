from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from db import get_session
from models.app_settings import AppSettings, AppSettingsRead, AppSettingsUpdate

router = APIRouter(
    prefix="/app-settings",
    tags=["app-settings"],
)


def _get_or_create_settings(session: Session) -> AppSettings:
    statement = select(AppSettings).order_by(col(AppSettings.created_at))
    settings = session.exec(statement).first()
    if settings:
        return settings
    settings = AppSettings()
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


@router.get("", response_model=AppSettingsRead)
def get_settings(session: Session = Depends(get_session)):
    return _get_or_create_settings(session)


@router.patch("", response_model=AppSettingsRead)
def update_settings(
    payload: AppSettingsUpdate,
    session: Session = Depends(get_session),
):
    settings = _get_or_create_settings(session)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    settings.updated_at = datetime.now(timezone.utc)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings
