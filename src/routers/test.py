from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class import AcademicClass, AcademicClassReadRaw
from models.academic_class_subject import (AcademicClassSubject,
                                           AcademicClassSubjectRead)
from models.academic_session import AcademicSession, AcademicSessionRead
from models.academic_term import AcademicTerm, AcademicTermRead
from models.enrollment import Enrollment, EnrollmentReadRaw
from models.report_card import ReportCard, ReportCardRead
from models.report_card_subject import ReportCardSubject, ReportCardSubjectRead
from models.student import Student, StudentReadRaw
from models.subject import Subject, SubjectRead

router = APIRouter(prefix="/test", tags=["test"])


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


@router.get("/academic_terms", response_model=list[AcademicTermRead])
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


@router.get("/report_cards", response_model=list[ReportCardRead])
def list_raw_report_cards(session: Session = Depends(get_session)):
    statement = select(ReportCard).order_by(col(ReportCard.created_at).desc())
    results = session.exec(statement).all()
    return results


@router.get(
    "/report_card_subjects",
    response_model=list[ReportCardSubjectRead],
)
def list_raw_report_card_subjects(
    session: Session = Depends(get_session),
):
    statement = select(ReportCardSubject).order_by(
        col(ReportCardSubject.created_at).desc()
    )
    results = session.exec(statement).all()
    return results
