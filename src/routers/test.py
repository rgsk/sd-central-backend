from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from db import get_session
from models.academic_class import AcademicClass, AcademicClassReadRaw
from models.academic_session import AcademicSession, AcademicSessionRead
from models.student import Student, StudentReadRaw

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/students", response_model=list[StudentReadRaw])
def list_raw_students(session: Session = Depends(get_session)):
    statement = select(Student)
    results = session.exec(statement).all()
    return results


@router.get("/academic_sessions", response_model=list[AcademicSessionRead])
def list_raw_academic_sessions(session: Session = Depends(get_session)):
    statement = select(AcademicSession)
    results = session.exec(statement).all()
    return results


@router.get("/academic_classes", response_model=list[AcademicClassReadRaw])
def list_raw_academic_classes(session: Session = Depends(get_session)):
    statement = select(AcademicClass)
    results = session.exec(statement).all()
    return results
