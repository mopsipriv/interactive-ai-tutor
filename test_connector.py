import asyncio
from database.db_connector import get_student_from_db
from database.db_connector import get_courses_from_db

async def test():
    print("Testing db_connector...\n")
    
    student = await get_student_from_db(1)
    print(f"Student: {student}\n")
    
    course = await get_courses_from_db(3)
    print(f"Course: {course}\n")

asyncio.run(test())