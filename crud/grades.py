"""Модуль с функциями добавления/удаления оценок"""
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import DatabaseError
from models import Grade, Student
from schemas.Grade import GradeCreate, GradeRead

from log.logger import grades_logger


async def create_grade(session: AsyncSession, data: GradeCreate) -> GradeRead | bool:
    """
        Создаёт новую оценку для студента по конкретному предмету.

        Проверки перед созданием:
            Существует ли студент с указанным student_id
            Не существует ли уже оценка по этому предмету у этого студента

        Args:
            session: Асинхронная сессия SQLAlchemy
            data: Данные для создания оценки (student_id, course_name, score, date и т.д.)

        Returns:
            GradeRead: Объект созданной оценки с присвоенным ID
            bool: False — если студент не найден или оценка по предмету уже существует
    """
    grades_logger.info(f"Creating grade for student_id={data.student_id},"
                       f" course={data.course_name}, grade = {data.score}")

    student = await session.execute(select(Student.id).where(Student.id == data.student_id))

    # Есть ли студент
    if student.scalars().first() is None:
        grades_logger.warning(f"Student with id={data.student_id} not found, cannot create grade")
        return False
    existing_grade = await session.execute(select(Grade.id).where(Grade.student_id == data.student_id,
                                                                  Grade.course_name == data.course_name))
    # Если оценка по предмету существует - не добавлять
    if existing_grade.scalars().one_or_none() is not None:
        grades_logger.warning(f"Grade for student_id={data.student_id},"
                              f" course={data.course_name} already exists")
        return False

    grade = Grade(**data.model_dump())
    try:
        session.add(grade)
        await session.commit()
        await session.refresh(grade)
        grades_logger.info(f"Grade {data.score} created  successfully for "
                           f"student_id={data.student_id},"f" course={data.course_name}")
        return GradeRead.model_validate(grade)

    except SQLAlchemyError as e:
        await session.rollback()
        grades_logger.error(f"Failed to create grade for student_id={data.student_id}: {e}", exc_info=True)
        raise DatabaseError("ERROR:Failed to add grade")
    except IntegrityError:
        await session.rollback()
        grades_logger.error(f"Grade violates constraints for student_id={data.student_id}: {e}", exc_info=True)
        raise DatabaseError("ERROR:Grade violates database constraints")


async def delete_grade(session: AsyncSession, grade_id: int) -> bool:
    """
            Создаёт новую оценку для студента по конкретному предмету.

            Args:
                session: Асинхронная сессия SQLAlchemy
                grade_id: Идентификатор по которому удаляется студент

            Returns:
                bool: True - если оценка удалена
                bool: False — если оценка не найдена
    """
    grades_logger.info(f"Deleting grade with id={grade_id}")
    try:

        result = await session.execute(select(Grade).where(Grade.id == grade_id))
        grade = result.scalar_one_or_none()

        # Если оценка в базе не нашлась
        if not grade:
            grades_logger.warning(f"Grade with id={grade_id} not found")
            return False

        await session.delete(grade)
        await session.commit()
        grades_logger.info(f"Grade with id={grade_id} deleted successfully")
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        grades_logger.error(f"Failed to delete grade with id={grade_id}: {e}", exc_info=True)
        raise DatabaseError("ERROR:Failed to delete grade")
