"""Модуль с pydantic-моделями для манипуляций с данными студентов"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from models import StudentStatus, StudentGrade

from schemas.ContactInfo import ContactInfoRead, ContactInfoUpdate
from schemas.Grade import GradeRead


class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    birth_date: date
    status: StudentStatus = StudentStatus.ACTIVE
    group: str

    contact: ContactInfoRead

    model_config = ConfigDict(from_attributes=True)


class StudentRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    birth_date: date
    status: StudentStatus = StudentStatus.ACTIVE
    group: str

    contact: ContactInfoRead
    grades: list[GradeRead] = []
    model_config = ConfigDict(from_attributes=True)


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    birth_date: Optional[date] = None
    status: Optional[StudentStatus] = None
    group: Optional[str] = None

    contact: Optional[ContactInfoUpdate] = None

    model_config = ConfigDict(from_attributes=True)


class StudentDelete(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)


class StudentFilter(BaseModel):
    last_name: Optional[str] = None
    score_present: Optional[StudentGrade] = None
    born_before: Optional[date] = None
    born_after: Optional[date] = None
    group: Optional[str] = None
    has_email: Optional[bool] = None

    limit: int = 10
    offset: int = 0
