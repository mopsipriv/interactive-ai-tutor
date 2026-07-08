from fastmcp import FastMCP
from database.db_connector import (
    get_all_students,
    get_student_by_course,
    get_all_courses,
    get_student_profile,
    enroll_student,
    update_grade,
    get_students_by_group
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
async def enroll_student_tool(student_id:int, course_id:int) ->list:
    """Enroll a student into a course"""
    return await enroll_student(student_id,course_id)

@mcp.tool
async def update_grade_tool(student_id:int, course_id:int, grade:int) ->list:
    """Update a students grade in course"""
    return await update_grade(student_id,course_id,grade)

@mcp.tool
async def get_students_by_group_tool(group_code:str) ->list:
    """Get all students by their group"""
    return await get_students_by_group(group_code)


if __name__=="__main__":
    mcp.run()