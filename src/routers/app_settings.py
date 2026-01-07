from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from db import get_session
from models.academic_class import AcademicClass
from models.academic_term import AcademicTerm
from models.app_settings import (SINGLETON_APP_SETTINGS_ID, AppSettings,
                                 AppSettingsRead, AppSettingsUpdate)

router = APIRouter(
    prefix="/app-settings",
    tags=["app-settings"],
)


def _get_or_create_settings(session: Session) -> AppSettings:
    statement = select(AppSettings).where(
        AppSettings.id == SINGLETON_APP_SETTINGS_ID
    )
    settings = session.exec(statement).one_or_none()
    if settings:
        return settings
    settings = AppSettings(id=SINGLETON_APP_SETTINGS_ID)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings


def _validate_defaults_match_session(
    session: Session,
    settings: AppSettings,
    update_data: dict,
) -> None:
    session_id = update_data.get(
        "default_academic_session_id",
        settings.default_academic_session_id,
    )
    term_id = update_data.get(
        "default_academic_term_id",
        settings.default_academic_term_id,
    )
    class_id = update_data.get(
        "default_academic_class_id",
        settings.default_academic_class_id,
    )
    if term_id is not None:
        if session_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Default academic session is required when default academic term is set"
                ),
            )
        term = session.exec(
            select(AcademicTerm).where(AcademicTerm.id == term_id)
        ).one_or_none()
        if not term:
            raise HTTPException(status_code=404, detail="Academic term not found")
        if term.academic_session_id != session_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Default academic term must belong to the default academic session"
                ),
            )
    if class_id is not None:
        if session_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Default academic session is required when default academic class is set"
                ),
            )
        academic_class = session.exec(
            select(AcademicClass).where(AcademicClass.id == class_id)
        ).one_or_none()
        if not academic_class:
            raise HTTPException(
                status_code=404, detail="Academic class not found"
            )
        if academic_class.academic_session_id != session_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Default academic class must belong to the default academic session"
                ),
            )


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
    _validate_defaults_match_session(session, settings, update_data)
    for key, value in update_data.items():
        setattr(settings, key, value)
    settings.updated_at = datetime.now(timezone.utc)
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings
