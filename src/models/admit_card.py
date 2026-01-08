from sqlmodel import SQLModel

from models.academic_term import AcademicTermRead
from models.datesheet_subject import DateSheetSubjectRead
from models.enrollment import EnrollmentRead


class AdmitCardResponse(SQLModel):
    enrollment: EnrollmentRead
    academic_term: AcademicTermRead
    datesheet_subjects: list[DateSheetSubjectRead]
