from typing_extensions import TypedDict

class State(TypedDict):
    student_id: int
    student_data: str
    
    course_id: int
    course_data: str

    enrollments: list
    is_allowed: bool

    final_text: str

    bot_analyze_text: str 
    
    filter_course: str

    enroll_student_name: str
    enroll_course_name: str
    enroll_result: str

