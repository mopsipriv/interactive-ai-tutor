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

async def get_student_enrollments(student_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT e.*, c.course_name, c.credit
               FROM enrollment e
               JOIN course c ON e.idcourse = c.idcourse
               WHERE e.idstudent = %s""",
            (student_id,)
        )
        result = await cur.fetchall()
    conn.close()
    return list(result) if result else []

async def check_eligibility(student_id: int, project_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            
            (student_id,student_id,project_id)
        )
        result= await cur.fetchall()
    conn.close()
    return list(result) if result else[]

async def get_all_students():
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute("SELECT * FROM student")
        result = await cur.fetchall()
    conn.close()
    return list(result) if result else []

async def get_student_by_course(course_name:str):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT s.fname,s.lname,e.status,e.grade,c.course_name 
            FROM enrollment e 
            JOIN course c ON e.idcourse= c.idcourse
            JOIN student s ON e.idstudent= s.idstudent
            WHERE c.course_name= %s""",
            (course_name,)
        )
        result=await cur.fetchall()
    conn.close()
    return list(result) if result else[]

async def enroll_student(student_id: int, course_id: int):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """INSERT INTO enrollment (idstudent, idcourse, status) 
                VALUES (%s, %s, 'planned')""",
                (student_id, course_id)
            )
        await conn.commit()
        conn.close()
        return "Student enrolled successfully"
    except Exception as e:
        return f"Error: {e}"
    
async def get_student_id_by_name(fname:str ,lname:str):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT idstudent FROM student WHERE fname= %s AND lname=%s""",
            (fname, lname)
        )
        result = await cur.fetchone()
    conn.close()
    if result:
        return result["idstudent"]
    else: 
        return None
    
async def get_course_id_by_name(course_name:str):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT idcourse FROM course WHERE course_name= %s""",
            (course_name,)
        )
        result = await cur.fetchone()
    conn.close()
    if result:
        return result["idcourse"]
    else: 
        return None
    
async def get_all_courses():
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT * FROM course"""
        )
        result=await cur.fetchall()
    conn.close()
    return list(result) if result else[]

async def update_grade(student_id:int, course_id:int, grade:int):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """UPDATE enrollment 
                SET grade=%s
                WHERE idstudent=%s AND idcourse=%s""",
                (grade, student_id, course_id, )
            )
            await conn.commit()
            conn.close()
        return "Student grade updated successfully"
    except Exception as e:
        return f"Error: {e}"

async def get_student_profile(student_id:int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT s.*, c.course_name, c.credit, e.status, e.grade
            FROM student s
            JOIN enrollment e ON s.idstudent = e.idstudent
            JOIN course c ON e.idcourse = c.idcourse
            WHERE s.idstudent = %s""",
            (student_id,)
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else[]

async def update_enrollment_status(student_id:int,course_id:int,status:str):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """UPDATE enrollment 
                SET status=%s
                WHERE idstudent=%s AND idcourse=%s""",
                (status, student_id, course_id, )
            )
        await conn.commit()
        conn.close()
        return "Students enrollment status updated successfully"
    except Exception as e:
        return f"Error: {e}"

async def get_students_by_group(group_code:str):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT s.fname, s.lname, s.student_number, gc.group_code, s.idstudent
            FROM student s
            JOIN student_group sg ON s.idstudent = sg.idstudent
            JOIN group_cohort gc ON sg.idgroup = gc.idgroup_cohort
            WHERE gc.group_code = %s""",
            (group_code,)
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else[]

async def get_teacher_by_email(email:str):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT * FROM teacher WHERE email=%s""",
            (email,)
        )
        result = await cur.fetchone()
    conn.close()
    return result if result else None

async def set_teacher_password(teacher_id:int, password_hash:str):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """UPDATE teacher 
                    SET password_hash=%s
                    WHERE idteacher=%s""",
                    (password_hash, teacher_id,)
            )
            await conn.commit()
            conn.close()
        return "Teacher's password updated successfully"
    except Exception as e:
        return f"Error: {e}"
    
async def get_student_by_number(student_number:int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT * FROM student WHERE student_number=%s""",
            (student_number,)
        )
        result = await cur.fetchone()
    conn.close()
    return result if result else None

async def set_student_password(student_id:int, password_hash:str):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """UPDATE student
                    SET password_hash=%s
                    WHERE idstudent=%s""",
                    (password_hash, student_id,)
            )
            await conn.commit()
            conn.close()
        return "Student's password updated successfully"
    except Exception as e:
        return f"Error: {e}"