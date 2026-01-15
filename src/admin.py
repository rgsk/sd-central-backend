from sqladmin import Admin, ModelView

from db import engine
from models.academic_class import AcademicClass
from models.academic_class_subject import AcademicClassSubject
from models.academic_session import AcademicSession
from models.academic_term import AcademicTerm
from models.app_settings import AppSettings
from models.enrollment import Enrollment
from models.report_card import ReportCard
from models.report_card_subject import ReportCardSubject
from models.student import Student
from models.subject import Subject
from models.user import User


class BaseModelView(ModelView):
    can_view_details = True
    page_size = 50


class AcademicClassAdmin(BaseModelView, model=AcademicClass):
    pass


class AcademicClassSubjectAdmin(BaseModelView, model=AcademicClassSubject):
    pass


class AcademicSessionAdmin(BaseModelView, model=AcademicSession):
    pass


class AcademicTermAdmin(BaseModelView, model=AcademicTerm):
    pass


class AppSettingsAdmin(BaseModelView, model=AppSettings):
    pass


class EnrollmentAdmin(BaseModelView, model=Enrollment):
    pass


class ReportCardAdmin(BaseModelView, model=ReportCard):
    pass


class ReportCardSubjectAdmin(BaseModelView, model=ReportCardSubject):
    pass


class StudentAdmin(BaseModelView, model=Student):
    pass


class SubjectAdmin(BaseModelView, model=Subject):
    pass


class UserAdmin(BaseModelView, model=User):
    pass


def setup_admin(app) -> Admin:
    admin = Admin(app, engine)
    admin.add_view(StudentAdmin)
    admin.add_view(EnrollmentAdmin)
    admin.add_view(AcademicClassAdmin)
    admin.add_view(AcademicSessionAdmin)
    admin.add_view(AcademicTermAdmin)
    admin.add_view(SubjectAdmin)
    admin.add_view(AcademicClassSubjectAdmin)
    admin.add_view(ReportCardAdmin)
    admin.add_view(ReportCardSubjectAdmin)
    admin.add_view(AppSettingsAdmin)
    admin.add_view(UserAdmin)
    return admin
