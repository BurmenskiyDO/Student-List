from enum import IntEnum, StrEnum
from typing import Optional

from sqlalchemy import ForeignKey, UniqueConstraint, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import date


class StudentGrade(IntEnum):
    POOR = 1
    DEFICIENT = 2
    SATISFACTORY = 3
    GOOD = 4
    EXCELLENT = 5

class StudentStatus(StrEnum):
    ACTIVE = "active"
    EXPELLED = "expelled"
    ACADEMIC_LEAVE = "academic_leave"
    GRADUATED = "graduated"


class Base(DeclarativeBase):
    pass


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    patronymic: Mapped[str | None] = mapped_column()
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[StudentStatus] = mapped_column(default=StudentStatus.ACTIVE)
    group: Mapped[str] = mapped_column(nullable=False)

    contact: Mapped["ContactInfo"] = relationship(uselist=False, back_populates="student",lazy="joined",cascade="all, delete-orphan")
    grades: Mapped[list["Grade"]] = relationship(back_populates="student",cascade="all, delete-orphan")


class ContactInfo(Base):
    __tablename__ = "contact_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=False)

    student: Mapped["Student"] = relationship(back_populates="contact")


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_name: Mapped[str] = mapped_column(nullable=False)
    score: Mapped[StudentGrade] = mapped_column(nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    student: Mapped["Student"] = relationship(back_populates="grades")

    __table_args__ = (UniqueConstraint("student_id", "course_name", name="uq_student_course"),)
