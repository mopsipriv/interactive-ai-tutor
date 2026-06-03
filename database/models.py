from pydantic import BaseModel

class StudentModel(BaseModel):
    idstudent: int
    student_number: str
    fname: str
    lname: str
    email: str
    study_right: str
    valid_from: str
    valid_until: str

class CourseModel(BaseModel):
    idcourse: int
    course_code: str
    course_name: str
    credit: int
    category: str

