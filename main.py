"""Основной модуль
Содержит API эндпоинты для работы с оценками студентов

Эндпоинты:
- DELETE /students/delete/{student_id}: удалить студента по ID.
- DELETE /students/delete_by_status/{status}: удалить студентов по статусу.
- PATCH /students/update/{student_id}: обновить информацию о студенте.
- POST /students/filter: получить список студентов по фильтрам.
- POST /grades/add: добавить оценку студенту.
- POST /grades/delete/{grade_id}: удалить оценку по ID.
"""

from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.grades import create_grade, delete_grade
from crud.students import create_student, delete_student, delete_students_by_status, update_student_info, \
    get_students_filtered

from db import get_session
from models import StudentStatus
from schemas.grade import GradeCreate, GradeRead
from schemas.student import StudentCreate, StudentRead, StudentUpdate, StudentFilter

app = FastAPI()


@app.post("/students/add", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def add_student(data: StudentCreate, session: AsyncSession = Depends(get_session)):
    return await create_student(session, data)


@app.delete("/students/delete/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student(student_id: int, session: AsyncSession = Depends(get_session)):
    deleted = await delete_student(session, student_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Student not found.")


@app.delete("/students/delete_by_status/{status}", status_code=status.HTTP_200_OK)
async def remove_students_by_status(student_status: StudentStatus,
                                    session: AsyncSession = Depends(get_session)):
    deleted_count = await delete_students_by_status(session, student_status)
    return {"deleted": deleted_count}


@app.patch("/students/update/{student_id}", response_model=StudentRead, status_code=status.HTTP_200_OK)
async def update_student(student_id: int, data: StudentUpdate, session: AsyncSession = Depends(get_session)):
    student = await update_student_info(session, student_id, data)
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Student not found.")
    return student


@app.get("/students/filter", response_model=List[StudentRead], status_code=status.HTTP_200_OK)
async def filter_students(filters: StudentFilter = Depends(), session: AsyncSession = Depends(get_session)):
    students = await get_students_filtered(session, filters)
    return students


@app.post("/grades/add", response_model=GradeRead, status_code=status.HTTP_201_CREATED)
async def add_grade(data: GradeCreate, session: AsyncSession = Depends(get_session)):
    grade = await create_grade(session, data)
    if not grade:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            detail="Student with matching id not found or grade already exists.")
    return grade


@app.delete("/grades/delete/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_grade(grade_id: int, session: AsyncSession = Depends(get_session)):
    deleted = await delete_grade(session, grade_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Grade not found.")
