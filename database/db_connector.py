import aiomysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "987654321",
    "db": "mydb"
}

async def get_student_from_db(student_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "SELECT * FROM student WHERE idstudent = %s",
            (student_id,)
        )
        result = await cur.fetchone()
    conn.close()
    return result if result else "Not found"

async def get_courses_from_db(course_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            "SELECT * FROM course WHERE idcourse = %s",
            (course_id,)
        )
        result = await cur.fetchone()
    conn.close()
    return result if result else "Not found"