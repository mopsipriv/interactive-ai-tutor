from fastmcp import FastMCP
from typing import Optional

from database.db_connector import (
    get_all_students,
    get_student_by_course,
    get_all_courses,
    get_student_profile,
    enroll_student,
    update_grade,
    get_students_by_group,
    get_course_id_by_name,
    get_student_id_by_name,
    update_enrollment_status,
    get_student_from_db,
    get_courses_from_db,
    get_student_enrollments,
    get_teacher_query_history,
    log_teacher_query
)

mcp = FastMCP("Tutor Server")

@mcp.tool
async def get_students_tool() -> list:
    """Get all students from the database"""
    return await get_all_students()

@mcp.tool
async def get_student_by_course_tool(course_name: str) -> list:
    """Get students enrolled in a specific course"""
    return await get_student_by_course(course_name)

@mcp.tool
async def get_all_courses_tool() -> list:
    """Get all courses from the database"""
    return await get_all_courses()

@mcp.tool
async def get_student_profile_tool(student_id:int) -> list:
    """Get full profile of a student including all courses"""
    return await get_student_profile(student_id)

@mcp.tool
async def enroll_student_tool(student_id:int, course_id:int) ->str:
    """Enroll a student into a course"""
    return await enroll_student(student_id,course_id)

@mcp.tool
async def update_grade_tool(student_id:int, course_id:int, grade:int) ->str:
    """Update a students grade in course"""
    return await update_grade(student_id,course_id,grade)

@mcp.tool
async def get_students_by_group_tool(group_code:str) ->list:
    """Get all students by their group"""
    return await get_students_by_group(group_code)

@mcp.tool
async def get_course_id_by_name_tool(course_name:str) -> Optional[int]:
    """Get course id by course name"""
    return await get_course_id_by_name(course_name)


@mcp.tool
async def get_student_id_by_name_tool(fname:str, lname:str) -> Optional[int]:
    """Get student id by first and last name"""
    return await get_student_id_by_name(fname, lname)

@mcp.tool
async def update_enrollment_status_tool(student_id:int,course_id:int,status:str) ->str:
    """Update enrollment status for a student in a course"""
    return await update_enrollment_status(student_id,course_id,status)

@mcp.tool
async def get_student_from_db_tool(student_id: int) ->list:
    """Get a single student by their id"""
    return await get_student_from_db(student_id)

@mcp.tool
async def get_courses_from_db_tool(course_id: int) ->list:
    """Get a single course by its id"""
    return await get_courses_from_db(course_id)

@mcp.tool
async def get_student_enrollments_tool(student_id: int) ->list:
    """Get all enrollments for a student with course names"""
    return await get_student_enrollments(student_id)

@mcp.tool
async def log_teacher_query_tool(teacher_id:int, query_text:str, intent:str, result:str)-> str:
    """Log a teacher's query for history tracking"""
    return await log_teacher_query(teacher_id,query_text,intent,result)

@mcp.tool
async def get_teacher_query_history_tool(teacher_id:int,limit=10)->list:
    """Function getting history"""
    return await get_teacher_query_history(teacher_id,limit)


if __name__=="__main__":
    mcp.run()