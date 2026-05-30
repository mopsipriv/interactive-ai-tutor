import asyncio

FAKE_STUDENTS = {
    1: {"id": 1, "name": "Mops ", "group_code": "TVT24", "telegram_id": 111},
    2: {"id": 2, "name": "Legenda", "group_code": "TVT25", "telegram_id": 222}
}

async def get_student_from_db(student_id: int):
    await asyncio.sleep(1)

    if student_id in FAKE_STUDENTS:
        return FAKE_STUDENTS[student_id]
    
    return "Not found"