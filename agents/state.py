from typing_extensions import TypedDict
from typing import Annotated
import operator

class State(TypedDict):
    students: list
    student_data: str
    filter_name: str

    course_id: int
    course_data: str

    enrollments: list

    is_allowed: bool

    final_text: str

    calendar_info: str
    student_messages: str
    bot_analyze_text: Annotated[str, operator.add]
    filter_course: str 

    enroll_student_name: str
    enroll_course_name: str
    enroll_result: str

    show_courses: bool
    courses_list: str

    grade_student_name: str
    grade_course_name: str
    grade_value: str
    grade_result: str

    student_profile: str

    status_student_name: str
    status_course_name: str
    status_value: str
    status_update_result: str

    risk_report: str

    filter_group: str

    group_report: str
    
    bulk_group_code: str
    bulk_course_name: str
    bulk_enroll_result: str

    eligibility_report: str

    student_recommendation: str

    course_report: str