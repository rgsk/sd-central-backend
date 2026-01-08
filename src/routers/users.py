from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class import AcademicClass
from models.academic_term import AcademicTerm
from models.user import (User, UserCreate, UserListResponse, UserRead,
                         UserUpdate)

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


def _validate_defaults_match_session(
    session: Session,
    user: User,
    update_data: dict,
) -> None:
    session_id = update_data.get(
        "default_academic_session_id",
        user.default_academic_session_id,
    )
    term_id = update_data.get(
        "default_academic_term_id",
        user.default_academic_term_id,
    )
    class_id = update_data.get(
        "default_academic_class_id",
        user.default_academic_class_id,
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
            raise HTTPException(
                status_code=404, detail="Academic term not found")
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


@router.post("", response_model=UserRead)
def create_user(
    user: UserCreate,
    session: Session = Depends(get_session),
):
    db_user = User(**user.model_dump())
    session.add(db_user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists",
        )
    session.refresh(db_user)
    return db_user


@router.get("", response_model=UserListResponse)
def list_users(
    session: Session = Depends(get_session),
    search: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    conditions = []
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        conditions.append(col(User.email).ilike(pattern))
    total = session.exec(
        select(func.count()).select_from(User).where(*conditions)
    ).one()
    users = session.exec(
        select(User)
        .where(*conditions)
        .order_by(col(User.created_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    items = [UserRead.model_validate(user) for user in users]
    return UserListResponse(total=total, items=items)


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.patch("/{user_id}", response_model=UserRead)
def partial_update_user(
    user_id: UUID,
    user: UserUpdate,
    session: Session = Depends(get_session),
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)
    _validate_defaults_match_session(session, db_user, update_data)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="User with this email already exists",
        )
    session.refresh(db_user)
    return db_user


@router.delete("/{user_id}")
def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(db_user)
    session.commit()
    return {"message": "User deleted"}
