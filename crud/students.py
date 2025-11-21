from sqlalchemy import delete, select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from models import StudentStatus, Student, ContactInfo, Grade
from schemas.ContactInfo import ContactInfoRead
from schemas.Student import StudentCreate, StudentRead, StudentUpdate, StudentFilter


async def create_student(session: AsyncSession, data: StudentCreate) -> StudentRead:
    student = Student(**data.model_dump(exclude={"contact"}, exclude_none=True))
    contact = ContactInfo(**data.contact.model_dump(exclude_none=True))
    student.contact = contact

    try:
        session.add(student)
        await session.commit()
        await session.refresh(student, attribute_names=["contact"])

        contact_dict = {
            "email": student.contact.email,
            "phone": student.contact.phone
        }

        student_read_dict = data.model_dump(exclude={"contact"}, exclude_none=True)
        student_read_dict.update({
            "id": student.id,
            "contact": contact_dict
        })
        return StudentRead.model_validate(student_read_dict)
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


async def delete_student(session: AsyncSession, student_id: int):
    student = await session.get(Student, student_id)

    if not student:
        return False
    try:
        await session.delete(student)
        await session.commit()
        return True
    except SQLAlchemyError as e:
        await session.rollback()
        raise e

    return True


async def delete_students_by_status(session: AsyncSession, status: StudentStatus) -> int:
    try:
        query = delete(Student).where(Student.status == status).returning(Student.id)
        result = await session.execute(query)

        deleted_count = len(result.scalars().all())
        await session.commit()
        return deleted_count
    except SQLAlchemyError as e:
        await session.rollback()
        raise e


async def update_student_info(session: AsyncSession, student_id: int,
                              data: StudentUpdate) -> StudentRead | None:
    try:
        student = await session.get(Student, student_id)
        if not student:
            return None

        update_data = data.model_dump(exclude_none=True)

        for key, value in update_data.items():
            if key != "contact":
                setattr(student, key, value)

        if "contact" in update_data:
            contact_data = update_data["contact"]
            if student.contact is None:
                student.contact = ContactInfo()
            for key, value in contact_data.items():
                setattr(student.contact, key, value)

        await session.commit()
        await session.refresh(student)

        return StudentRead.model_validate(student)

    except SQLAlchemyError as e:
        await session.rollback()
        raise e


async def get_students_filtered(session: AsyncSession, filters: StudentFilter) -> list[StudentRead]:
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
    if filters.score_threshold is not None:
        subquery = (select(Grade.student_id).group_by(Grade.student_id)
            .having(func.min(Grade.score) >= filters.score_threshold.value)
            .subquery()
        )
        filter_conditions.append(Student.id.in_(select(subquery.c.student_id)))

    query = select(Student).options(joinedload(Student.grades))
    if filter_conditions:
        query = query.where(*filter_conditions)

    query = query.offset(filters.offset).limit(filters.limit)

    result = await session.execute(query)
    students = result.unique().scalars().all()

    return [StudentRead.model_validate(student) for student in students]
