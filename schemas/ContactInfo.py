from typing import Optional
from pydantic import BaseModel, ConfigDict


class ContactInfoRead(BaseModel):
    email: Optional[str] = None
    phone: str

    model_config = ConfigDict(from_attributes=True)