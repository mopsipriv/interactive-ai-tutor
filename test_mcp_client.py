import asyncio
from fastmcp import Client

async def test():
    async with Client("http://127.0.0.1:8000/mcp") as client:
        courses = await client.call_tool("get_all_courses_tool", {})
        print("Courses:", courses)
        
        students = await client.call_tool("get_students_tool", {})
        print("Students:", students)
        
        profile = await client.call_tool("get_student_profile_tool", {"student_id": 1})
        print("Profile:", profile)

asyncio.run(test())