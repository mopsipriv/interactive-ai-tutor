from pydantic import BaseModel

class StudentModel(BaseModel):
    id: int
    name: str
    group_code: str
    telegram_id: int

class CourseModel(BaseModel):
    id: int
    title: str
    teacher_name: str

