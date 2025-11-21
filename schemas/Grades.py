from pydantic import BaseModel


class GradeRead(BaseModel):
    subject: str
    score: int