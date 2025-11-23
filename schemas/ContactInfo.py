"""Модуль с pydantic-моделями для манипуляций с контактной информацией студентов"""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ContactInfoRead(BaseModel):
    email: Optional[str] = None
    phone: str

    model_config = ConfigDict(from_attributes=True)


class ContactInfoUpdate(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
