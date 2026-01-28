import json
import subprocess
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class import AcademicClass, AcademicClassReadRaw
from models.academic_class_subject import (AcademicClassSubject,
                                           AcademicClassSubjectRead)
from models.academic_class_subject_term import (AcademicClassSubjectTerm,
                                                AcademicClassSubjectTermRead)
from models.academic_session import AcademicSession, AcademicSessionRead
from models.academic_term import AcademicTerm, AcademicTermReadRaw
from models.date_sheet import DateSheet, DateSheetReadRaw
from models.date_sheet_subject import DateSheetSubject, DateSheetSubjectReadRaw
from models.enrollment import Enrollment, EnrollmentReadRaw
from models.report_card import ReportCard, ReportCardRead
from models.report_card_subject import (ReportCardSubject,
                                        ReportCardSubjectReadRaw)
from models.student import Student, StudentReadRaw
from models.subject import Subject, SubjectRead
from models.user import User, UserReadRaw

router = APIRouter(prefix="/test", tags=["test"])

SEED_DATA_DIR = Path(__file__).resolve().parents[2] / "seeders" / "data"
REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND_ERROR_MESSAGE = "Command failed."


def _load_seed_data() -> dict[str, object]:
    if not SEED_DATA_DIR.exists():
        raise HTTPException(
            status_code=404,
            detail="Seed data directory not found.",
        )

    seed_data: dict[str, object] = {}
    for json_file in sorted(SEED_DATA_DIR.glob("*.json")):
        try:
            seed_data[json_file.stem] = json.loads(json_file.read_text())
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid JSON in {json_file.name}.",
            ) from exc

    return seed_data


@router.get("/seed_data")
def list_seed_data():
    return _load_seed_data()


@router.get("/db_data")
def list_db_data(session: Session = Depends(get_session)):
    return {
        "students": session.exec(
            select(Student).order_by(col(Student.created_at).desc())
        ).all(),
        "enrollments": session.exec(
            select(Enrollment).order_by(col(Enrollment.created_at).desc())
        ).all(),
        "academic_sessions": session.exec(
            select(AcademicSession).order_by(
                col(AcademicSession.created_at).desc()
            )
        ).all(),
        "academic_classes": session.exec(
            select(AcademicClass).order_by(
                col(AcademicClass.created_at).desc()
            )
        ).all(),
        "academic_terms": session.exec(
            select(AcademicTerm).order_by(
                col(AcademicTerm.created_at).desc()
            )
        ).all(),
        "subjects": session.exec(
            select(Subject).order_by(col(Subject.created_at).desc())
        ).all(),
        "academic_class_subjects": session.exec(
            select(AcademicClassSubject).order_by(
                col(AcademicClassSubject.created_at).desc()
            )
        ).all(),
        "academic_class_subject_terms": session.exec(
            select(AcademicClassSubjectTerm).order_by(
                col(AcademicClassSubjectTerm.created_at).desc()
            )
        ).all(),
        "report_cards": session.exec(
            select(ReportCard).order_by(col(ReportCard.created_at).desc())
        ).all(),
        "report_card_subjects": session.exec(
            select(ReportCardSubject).order_by(
                col(ReportCardSubject.created_at).desc()
            )
        ).all(),
        "date_sheets": session.exec(
            select(DateSheet).order_by(col(DateSheet.created_at).desc())
        ).all(),
        "date_sheet_subjects": session.exec(
            select(DateSheetSubject).order_by(
                col(DateSheetSubject.created_at).desc()
            )
        ).all(),
        "users": session.exec(
            select(User).order_by(col(User.created_at).desc())
        ).all(),
    }


@router.get("/students", response_model=list[StudentReadRaw])
def list_raw_students(session: Session = Depends(get_session)):
    statement = select(Student).order_by(col(Student.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get("/enrollments", response_model=list[EnrollmentReadRaw])
def list_raw_enrollments(session: Session = Depends(get_session)):
    statement = select(Enrollment).order_by(
        col(Enrollment.created_at).desc()
    )
    results = session.exec(statement).all()
    return results


@router.get("/academic_sessions", response_model=list[AcademicSessionRead])
def list_raw_academic_sessions(session: Session = Depends(get_session)):
    statement = select(AcademicSession).order_by(
        col(AcademicSession.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get("/academic_classes", response_model=list[AcademicClassReadRaw])
def list_raw_academic_classes(session: Session = Depends(get_session)):
    statement = select(AcademicClass).order_by(
        col(AcademicClass.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get("/academic_terms", response_model=list[AcademicTermReadRaw])
def list_raw_academic_terms(session: Session = Depends(get_session)):
    statement = select(AcademicTerm).order_by(
        col(AcademicTerm.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get("/subjects", response_model=list[SubjectRead])
def list_raw_subjects(session: Session = Depends(get_session)):
    statement = select(Subject).order_by(col(Subject.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get(
    "/academic_class_subjects",
    response_model=list[AcademicClassSubjectRead],
)
def list_raw_academic_class_subjects(
    session: Session = Depends(get_session),
):
    statement = select(AcademicClassSubject).order_by(
        col(AcademicClassSubject.created_at).desc()
    )
    results = session.exec(statement).all()
    return results


@router.get(
    "/academic_class_subject_terms",
    response_model=list[AcademicClassSubjectTermRead],
)
def list_raw_academic_class_subject_terms(
    session: Session = Depends(get_session),
):
    statement = select(AcademicClassSubjectTerm).order_by(
        col(AcademicClassSubjectTerm.created_at).desc()
    )
    results = session.exec(statement).all()
    return results


@router.get("/report_cards", response_model=list[ReportCardRead])
def list_raw_report_cards(session: Session = Depends(get_session)):
    statement = select(ReportCard).order_by(col(ReportCard.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get(
    "/report_card_subjects",
    response_model=list[ReportCardSubjectReadRaw],
)
def list_raw_report_card_subjects(
    session: Session = Depends(get_session),
):
    statement = select(ReportCardSubject).order_by(
        col(ReportCardSubject.created_at).desc()
    )
    results = session.exec(statement).all()
    return results


@router.get("/date_sheets", response_model=list[DateSheetReadRaw])
def list_raw_date_sheets(session: Session = Depends(get_session)):
    statement = select(DateSheet).order_by(col(DateSheet.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get(
    "/date_sheet_subjects",
    response_model=list[DateSheetSubjectReadRaw],
)
def list_raw_date_sheet_subjects(
    session: Session = Depends(get_session),
):
    statement = select(DateSheetSubject).order_by(
        col(DateSheetSubject.created_at).desc()
    )
    results = session.exec(statement).all()
    return results


@router.get("/users", response_model=list[UserReadRaw])
def list_raw_users(session: Session = Depends(get_session)):
    statement = select(User).order_by(col(User.created_at).desc())
    results = session.exec(statement).all()
    return results


def _run_command(command: list[str]) -> dict[str, str]:
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    combined_output = f"{result.stdout}{result.stderr}"
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": COMMAND_ERROR_MESSAGE,
                "command": " ".join(command),
                "output": combined_output,
            },
        )
    return {
        "status": "ok",
        "command": " ".join(command),
        "output": combined_output,
    }


@router.post("/reset_db")
def reset_db():
    result = _run_command(["make", "reset_db"])
    time.sleep(1)
    return result


@router.post("/migrate_db")
def migrate_db():
    return _run_command(["make", "migrate_db"])


@router.post("/seed_db")
def seed_db(folder: str = Query(..., min_length=1)):
    return _run_command(["make", "seed_db", folder])


@router.post("/verify_seed")
def verify_seed(
    folder: str = Query(..., min_length=1),
    logical_compare: bool = Query(False),
):
    command = ["make", "verify_seed"]
    if logical_compare:
        command.append("LOGICAL_COMPARE=1")
    command.append(folder)
    return _run_command(command)


@router.post("/firebase_custom_token")
def firebase_custom_token(email: str = Query(..., min_length=1)):
    return _run_command(
        ["python", "scripts/create_firebase_custom_token.py", email]
    )
