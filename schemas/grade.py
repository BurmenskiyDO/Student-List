"""Модуль с pydantic-моделями для манипуляций с оценками студентов"""
from pydantic import BaseModel, ConfigDict
from datetime import date

from models import StudentGrade


class GradeRead(BaseModel):
    student_id:int
    course_name: str
    score: StudentGrade
    date: date

    model_config = ConfigDict(from_attributes=True)

class GradeCreate(BaseModel):
    student_id: int
    course_name: str
    score: StudentGrade
    date: date

    model_config = ConfigDict(from_attributes=True)