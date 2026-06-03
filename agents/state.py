from typing_extensions import TypedDict

class State(TypedDict):
    student_id: int
    student_data: str
    
    course_id: int
    course_data: str

    final_text: str