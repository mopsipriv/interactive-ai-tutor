from fastmcp import FastMCP
from database.db_connector import (
    get_all_students,
    get_student_by_course,
    get_all_courses,
    get_student_profile
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

if __name__=="__main__":
    mcp.run()