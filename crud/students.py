"""Модуль реализует функции для добавления/изменения/удаления/фильтрации студентов"""
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from exceptions import DatabaseError
from models import StudentStatus, Student, ContactInfo, Grade
from schemas.ContactInfo import ContactInfoRead
from schemas.Student import StudentCreate, StudentRead, StudentUpdate, StudentFilter

from log.logger import students_logger


async def create_student(session: AsyncSession, data: StudentCreate) -> StudentRead:
    """
        Создаёт нового студента вместе с контактной информацией.

        Args:
            session: Асинхронная сессия SQLAlchemy
            data: Данные для создания студента (включая вложенный объект contact)

        Returns:
            StudentRead: Полная модель созданного студента с ID и контактными данными
        Note:
            Поле contact создаётся как отдельная связанная запись
            Используется exclude_none=True — пустые поля не сохраняются
            После commit происходит refresh с подгрузкой контакта
    """
    students_logger.info(f"Creating student:")
    student = Student(**data.model_dump(exclude={"contact"}, exclude_none=True))
    contact = ContactInfo(**data.contact.model_dump(exclude_none=True))
    student.contact = contact

    try:
        session.add(student)
        await session.commit()
        await session.refresh(student, attribute_names=["contact"])

        contact_dict = ContactInfoRead.model_validate(student.contact).model_dump(exclude_none=True)


        student_read_dict = data.model_dump(exclude={"contact"}, exclude_none=True)
        student_read_dict.update({
            "id": student.id,
            "contact": contact_dict
        })
        students_logger.info(f"Student created successfully with id={student.id}")
        return StudentRead.model_validate(student_read_dict)
    except SQLAlchemyError as e:
        await session.rollback()
        students_logger.error(f"Failed to create student: {e}", exc_info=True)
        raise DatabaseError("ERROR:Student creation failed")


async def delete_student(session: AsyncSession, student_id: int) -> bool:
    """
        Удаляет студента по ID (с каскадным удалением контакта и оценок).

        Args:
            session: Асинхронная сессия SQLAlchemy
            student_id: Уникальный идентификатор студента

        Returns:
            bool: True — если студент был найден и удалён, False — если не найден
    """
    students_logger.info(f"Deleting student with id={student_id}")
    student = await session.get(Student, student_id)

    if not student:
        students_logger.warning(f"Student with id={student_id} not found")
        return False

    try:
        await session.delete(student)
        await session.commit()
        students_logger.info(f"Student with id={student_id} deleted successfully")
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        students_logger.error(f"Failed to delete student with id={student_id}: {e}", exc_info=True)
        raise DatabaseError("ERROR:Student deletion failed")


async def delete_students_by_status(session: AsyncSession, status: StudentStatus) -> int:
    """
        Массово удаляет всех студентов с указанным статусом.

        Args:
            session: Асинхронная сессия SQLAlchemy
            status: Значение IntEnum StudentStatus(ACTIVE,ACADEMIC_LEAVE,EXPELLED,GRADUATED)

        Returns:
            int: Количество удалённых студентов
    """
    students_logger.info(f"Deleting students with status={status}")
    try:
        query = delete(Student).where(Student.status == status).returning(Student.id)
        result = await session.execute(query)

        deleted_count = len(result.scalars().all())
        await session.commit()
        students_logger.info(f"Deleted {deleted_count} students with status={status}")
        return deleted_count
    except SQLAlchemyError as e:
        await session.rollback()
        students_logger.error(f"Failed to delete students by status={status}: {e}", exc_info=True)
        raise DatabaseError("ERROR:Student deletion by status failed")


async def update_student_info(session: AsyncSession, student_id: int,
                              data: StudentUpdate) -> StudentRead | None:
    """
        Частично обновляет данные студента и его контактной информации.

        Args:
            session: Асинхронная сессия SQLAlchemy
            student_id: ID студента для обновления
            data: Обновляемые поля (все поля опциональны, включая вложенный contact)

        Returns:
            StudentRead: Обновлённый объект студента или None, если студент не найден
    """
    students_logger.info(f"Updating student with id={student_id}, data={data}")
    try:
        student = await session.get(Student, student_id,
                                    options=[selectinload(Student.contact), selectinload(Student.grades)])

        if not student:
            students_logger.info(f"Student with id={student_id} not found")
            return None
        update_data = data.model_dump(exclude_none=True)

        #Обновление всех полей кроме вложенного contact
        for key, value in update_data.items():
            if key != "contact":
                setattr(student, key, value)

        #Обновление полей из contact
        if "contact" in update_data:
            contact_data = update_data["contact"]
            if student.contact is None:
                student.contact = ContactInfo()
            for key, value in contact_data.items():
                setattr(student.contact, key, value)

        await session.commit()
        students_logger.info(f"Student with id={student_id} updated successfully")
        return StudentRead.model_validate(student)

    except SQLAlchemyError as e:
        await session.rollback()
        students_logger.error(f"Failed to update student with id={student_id}: {e}", exc_info=True)
        raise DatabaseError("ERROR:Student update failed")


async def get_students_filtered(session: AsyncSession, filters: StudentFilter) -> list[StudentRead]:
    """
        Возвращает отфильтрованный список студентов с подгруженными оценками.

        Поддерживаемые фильтры:
            born_after / born_before — диапазон дат рождения
            group, last_name — точное совпадение
            has_email — есть ли email в контактах
            score_present — есть ли оценка с конкретным значением
            offset / limit — пагинация

        Args:
            session: Асинхронная сессия SQLAlchemy
            filters: Объект с параметрами фильтрации (все поля опциональны)

        Returns:
            list[StudentRead]: Список студентов, удовлетворяющих условиям
    """
    students_logger.info(f"Filtering students with filters=[{filters}]")

    #Сбор всех условий для фильтрации в список
    filter_conditions = []
    if filters.born_after is not None:
        filter_conditions.append(Student.birth_date > filters.born_after)
    if filters.born_before is not None:
        filter_conditions.append(Student.birth_date < filters.born_before)
    if filters.group is not None:
        filter_conditions.append(Student.group == filters.group)
    if filters.last_name is not None:
        filter_conditions.append(Student.last_name == filters.last_name)
    if filters.has_email is not None:
        if filters.has_email:
            filter_conditions.append(Student.contact.has(ContactInfo.email.isnot(None)))
        else:
            filter_conditions.append(Student.contact.has(ContactInfo.email.is_(None)))
    if filters.score_present is not None:
        subquery = select(Grade.student_id).where(Grade.score == filters.score_present)
        filter_conditions.append(Student.id.in_(subquery))

    try:
        query = select(Student).options(joinedload(Student.grades))
        #При наличии фильтров, добавить их в запрос
        if filter_conditions:
            query = query.where(*filter_conditions)
        #Пагинация - при отсутствии переданных параметров, будут установлены по умолчанию из модели filters
        query = query.offset(filters.offset).limit(filters.limit)

        result = await session.execute(query)
        students = result.unique().scalars().all()

        students_logger.info(f"Filtered {len(students)} students")
        return [StudentRead.model_validate(student) for student in students]
    except SQLAlchemyError as e:
        students_logger.error(f"Failed to filter students: {e}", exc_info=True)
        raise DatabaseError("ERROR:Student filtering failed")
