import aiomysql
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_NAME", "peppi_db")
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

"""async def check_eligibility(student_id: int, project_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            
            (student_id,student_id,project_id)
        )
        result= await cur.fetchall()
    conn.close()
    return list(result) if result else[]"""

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
    
async def log_teacher_query(teacher_id:int, query_text:str, intent:str, result:str):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """INSERT INTO teacher_query_log (idteacher, query_text, intent, result, created_at) 
                VALUES (%s, %s, %s, %s, %s) """,
                (teacher_id, query_text, intent, result, datetime.now(),)
            )
            await conn.commit()
            conn.close()
        return "Logged successfully"
    except Exception as e:
        return f"Error: {e}"
    
async def get_teacher_query_history(teacher_id:int,limit=10):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT * FROM teacher_query_log WHERE idteacher= %s
            ORDER BY created_at DESC LIMIT %s""",
            (teacher_id,limit,)
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else []

async def get_curriculum(program_code:str):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT cu.semester, cu.course_type, c.course_name, c.course_code, c.credit
            FROM curriculum cu
            JOIN course c ON cu.idcourse = c.idcourse
            WHERE cu.program_code = %s
            ORDER BY cu.semester """,
            (program_code,)
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else []

async def get_student_curriculum_progress(student_id:int, program_code:str):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT cu.semester, cu.course_type, cu.idcourse, c.course_name, c.course_code, c.credit
            FROM curriculum cu
            JOIN course c ON cu.idcourse = c.idcourse
            WHERE cu.program_code = %s
            ORDER BY cu.semester""",
            (program_code,)
        )
        curriculum = await cur.fetchall()
        

        await cur.execute(
            """SELECT idcourse, status, grade
            FROM enrollment
            WHERE idstudent = %s""",
            (student_id,)
        )
        enrollments = await cur.fetchall()
    
    conn.close()
    
    enrollment_map = {}
    for e in enrollments:
        enrollment_map[e["idcourse"]] = {"status": e["status"], "grade": e["grade"]}
    
    result = []
    for course in curriculum:
        idcourse = course["idcourse"]
        if idcourse in enrollment_map:
            course["enrollment_status"] = enrollment_map[idcourse]["status"]
            course["grade"] = enrollment_map[idcourse]["grade"]
        else:
            course["enrollment_status"] = "not_enrolled"
            course["grade"] = None
        result.append(course)
    
    return result if result else []


async def get_course_analytics():
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT c.course_name, c.course_code,
                COUNT(*) as total_students,
                AVG(e.grade) as avg_grade,
                SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as completed_count
                FROM enrollment e
                JOIN course c ON e.idcourse = c.idcourse
                GROUP BY e.idcourse, c.course_name, c.course_code
                ORDER BY c.course_code"""
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else []


async def get_group_analytics(group_code: str):
    students = await get_students_by_group(group_code)
    if not students:
        return []
    
    conn = await aiomysql.connect(**DB_CONFIG)
    all_credits = []
    
    async with conn.cursor(aiomysql.DictCursor) as cur:
        for student in students:
            await cur.execute(
                """SELECT SUM(c.credit) as credits_earned
                FROM enrollment e
                JOIN course c ON e.idcourse = c.idcourse
                WHERE e.idstudent = %s AND e.status = 'completed'""",
                (student["idstudent"],)
            )
            result = await cur.fetchone()
            credits = result["credits_earned"] or 0
            all_credits.append(credits)
    
    conn.close()
    
    avg_credits = sum(all_credits) / len(students)
    
    return {
        "group_code": group_code,
        "total_students": len(students),
        "avg_credits_earned": round(avg_credits, 1)
    }


async def get_students_by_teacher(teacher_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT DISTINCT s.*
            FROM student s
            JOIN student_group sg ON s.idstudent = sg.idstudent
            JOIN group_cohort gc ON sg.idgroup = gc.idgroup_cohort
            WHERE gc.idteacher = %s""",
            (teacher_id,)
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else []


async def get_teacher_groups(teacher_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT gc.group_code, COUNT(DISTINCT sg.idstudent) as student_count
            FROM group_cohort gc
            LEFT JOIN student_group sg ON gc.idgroup_cohort = sg.idgroup
            WHERE gc.idteacher = %s
            GROUP BY gc.group_code""",
            (teacher_id,)
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else []

async def create_enrollment_request(student_id:int, course_id:int):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """INSERT INTO enrollment_request (idstudent, idcourse, status,requested_at)
                VALUES(%s,%s,'pending',%s)""",
                (student_id, course_id, datetime.now(),)
            )
            await conn.commit()
            conn.close()
        return "Create successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_pending_requests(teacher_id: int):
    conn = await aiomysql.connect(**DB_CONFIG)
    async with conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(
            """SELECT er.idrequest, er.idstudent, s.fname, s.lname, er.idcourse, 
                      c.course_code, c.course_name, er.status, er.requested_at
            FROM enrollment_request er
            JOIN student s ON er.idstudent = s.idstudent
            JOIN course c ON er.idcourse = c.idcourse
            JOIN student_group sg ON s.idstudent = sg.idstudent
            JOIN group_cohort gc ON sg.idgroup = gc.idgroup_cohort
            WHERE er.status = 'pending' AND gc.idteacher = %s
            ORDER BY er.requested_at ASC""",
            (teacher_id,)
        )
        result = await cur.fetchall()
    conn.close()
    return result if result else []

async def approve_request(request_id: int):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT idstudent, idcourse 
                   FROM enrollment_request 
                   WHERE idrequest = %s AND status = 'pending'""",
                (request_id,)
            )
            req = await cur.fetchone()

            if not req:
                conn.close()
                return "Error: Request not found or already processed"

            student_id = req["idstudent"]
            course_id = req["idcourse"]

            await cur.execute(
                """UPDATE enrollment_request 
                   SET status = 'approved', reviewed_at = %s 
                   WHERE idrequest = %s""",
                (datetime.now(), request_id)
            )

            await cur.execute(
                """INSERT INTO enrollment (idstudent, idcourse, status) 
                   VALUES (%s, %s, 'ongoing')""",
                (student_id, course_id)
            )

            await conn.commit()
            conn.close()
        return "Request approved and student enrolled successfully"
    except Exception as e:
        return f"Error: {e}"


async def reject_request(request_id:int):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """UPDATE enrollment_request
                SET status= 'rejected', reviewed_at=%s
                WHERE idrequest=%s""",
                (datetime.now(),request_id,)
            )
            await conn.commit()
            conn.close()
        return "Request is rejected successfully"
    except Exception as e:
        return f"Error: {e}"
    