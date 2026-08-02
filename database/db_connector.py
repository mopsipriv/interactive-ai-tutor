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

_pool = None


async def get_pool():
    """
    Returns a shared connection pool, creating it on first use.
    minsize/maxsize can be tuned; 1-10 is fine for a small tutoring system.
    """
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            minsize=1,
            maxsize=10,
            **DB_CONFIG
        )
    return _pool


async def close_pool():
    """Call this on application shutdown to release all connections cleanly."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


async def get_student_from_db(student_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM student WHERE idstudent = %s",
                (student_id,)
            )
            result = await cur.fetchone()
    return result if result else "Not found"


async def get_courses_from_db(course_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM course WHERE idcourse = %s",
                (course_id,)
            )
            result = await cur.fetchone()
    return result if result else "Not found"


async def get_student_enrollments(student_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT e.*, c.course_name, c.credit
                   FROM enrollment e
                   JOIN course c ON e.idcourse = c.idcourse
                   WHERE e.idstudent = %s""",
                (student_id,)
            )
            result = await cur.fetchall()
    return list(result) if result else []


async def get_all_students():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM student")
            result = await cur.fetchall()
    return list(result) if result else []


async def get_student_by_course(course_name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT s.fname,s.lname,e.status,e.grade,c.course_name 
                FROM enrollment e 
                JOIN course c ON e.idcourse= c.idcourse
                JOIN student s ON e.idstudent= s.idstudent
                WHERE c.course_name= %s""",
                (course_name,)
            )
            result = await cur.fetchall()
    return list(result) if result else []


async def enroll_student(student_id: int, course_id: int):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """INSERT INTO enrollment (idstudent, idcourse, status) 
                    VALUES (%s, %s, 'planned')""",
                    (student_id, course_id)
                )
                await conn.commit()
        return "Student enrolled successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_student_id_by_name(fname: str, lname: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT idstudent FROM student WHERE fname= %s AND lname=%s""",
                (fname, lname)
            )
            result = await cur.fetchone()
    if result:
        return result["idstudent"]
    else:
        return None


async def get_course_id_by_name(course_name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT idcourse FROM course WHERE course_name= %s""",
                (course_name,)
            )
            result = await cur.fetchone()
    if result:
        return result["idcourse"]
    else:
        return None


async def get_all_courses():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("""SELECT * FROM course""")
            result = await cur.fetchall()
    return list(result) if result else []


async def update_grade(student_id: int, course_id: int, grade: int):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """UPDATE enrollment 
                    SET grade=%s
                    WHERE idstudent=%s AND idcourse=%s""",
                    (grade, student_id, course_id,)
                )
                await conn.commit()
        return "Student grade updated successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_student_profile(student_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
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
    return result if result else []


async def update_enrollment_status(student_id: int, course_id: int, status: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """UPDATE enrollment 
                    SET status=%s
                    WHERE idstudent=%s AND idcourse=%s""",
                    (status, student_id, course_id,)
                )
                await conn.commit()
        return "Students enrollment status updated successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_students_by_group(group_code: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
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
    return result if result else []


async def get_teacher_by_email(email: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT * FROM teacher WHERE email=%s""",
                (email,)
            )
            result = await cur.fetchone()
    return result if result else None


async def set_teacher_password(teacher_id: int, password_hash: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """UPDATE teacher 
                        SET password_hash=%s
                        WHERE idteacher=%s""",
                    (password_hash, teacher_id,)
                )
                await conn.commit()
        return "Teacher's password updated successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_student_by_number(student_number: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT * FROM student WHERE student_number=%s""",
                (student_number,)
            )
            result = await cur.fetchone()
    return result if result else None


async def set_student_password(student_id: int, password_hash: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """UPDATE student
                        SET password_hash=%s
                        WHERE idstudent=%s""",
                    (password_hash, student_id,)
                )
                await conn.commit()
        return "Student's password updated successfully"
    except Exception as e:
        return f"Error: {e}"


async def log_teacher_query(teacher_id: int, query_text: str, intent: str, result: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """INSERT INTO teacher_query_log (idteacher, query_text, intent, result, created_at) 
                    VALUES (%s, %s, %s, %s, %s) """,
                    (teacher_id, query_text, intent, result, datetime.now(),)
                )
                await conn.commit()
        return "Logged successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_teacher_query_history(teacher_id: int, limit=10):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT * FROM teacher_query_log WHERE idteacher= %s
                ORDER BY created_at DESC LIMIT %s""",
                (teacher_id, limit,)
            )
            result = await cur.fetchall()
    return result if result else []


async def get_curriculum(program_code: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT cu.year_of_study, cu.course_type, c.course_name, c.course_code, c.credit
                FROM curriculum cu
                JOIN course c ON cu.idcourse = c.idcourse
                WHERE cu.program_code = %s
                ORDER BY cu.year_of_study """,
                (program_code,)
            )
            result = await cur.fetchall()
    return result if result else []


async def get_student_curriculum_progress(student_id: int, program_code: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT cu.year_of_study, cu.course_type, cu.idcourse, c.course_name, c.course_code, c.credit
                FROM curriculum cu
                JOIN course c ON cu.idcourse = c.idcourse
                WHERE cu.program_code = %s
                ORDER BY cu.year_of_study""",
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
    pool = await get_pool()
    async with pool.acquire() as conn:
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
    return result if result else []


async def get_group_analytics(group_code: str):
    students = await get_students_by_group(group_code)
    if not students:
        return []

    pool = await get_pool()
    all_credits = []

    async with pool.acquire() as conn:
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

    avg_credits = sum(all_credits) / len(students)

    return {
        "group_code": group_code,
        "total_students": len(students),
        "avg_credits_earned": round(avg_credits, 1)
    }


async def get_students_by_teacher(teacher_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
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
    return result if result else []


async def get_teacher_groups(teacher_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
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
    return result if result else []


async def create_enrollment_request(student_id: int, course_id: int):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """INSERT INTO enrollment_request (idstudent, idcourse, status,requested_at)
                    VALUES(%s,%s,'pending',%s)""",
                    (student_id, course_id, datetime.now(),)
                )
                await conn.commit()
        return "Create successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_pending_requests(teacher_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT er.idrequest, er.idstudent, s.fname, s.lname, er.idcourse, 
                    c.course_code, c.course_name, er.status, er.requested_at,
                    gc.group_code 
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
    return result if result else []


async def verify_request_ownership(request_id: int, teacher_id: int):
    """Check that a pending request belongs to a student in this teacher's group"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT er.idrequest
                   FROM enrollment_request er
                   JOIN student s ON er.idstudent = s.idstudent
                   JOIN student_group sg ON s.idstudent = sg.idstudent
                   JOIN group_cohort gc ON sg.idgroup = gc.idgroup_cohort
                   WHERE er.idrequest = %s AND gc.idteacher = %s""",
                (request_id, teacher_id)
            )
            result = await cur.fetchone()
    return result is not None


async def approve_request(request_id: int, teacher_id: int):
    try:
        owns = await verify_request_ownership(request_id, teacher_id)
        if not owns:
            return "Error: You can only approve requests from your own students"

        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """SELECT idstudent, idcourse 
                       FROM enrollment_request 
                       WHERE idrequest = %s AND status = 'pending'""",
                    (request_id,)
                )
                req = await cur.fetchone()

                if not req:
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
        return "Request approved and student enrolled successfully"
    except Exception as e:
        return f"Error: {e}"


async def reject_request(request_id: int, teacher_id: int):
    try:
        owns = await verify_request_ownership(request_id, teacher_id)
        if not owns:
            return "Error: You can only reject requests from your own students"

        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """UPDATE enrollment_request
                    SET status= 'rejected', reviewed_at=%s
                    WHERE idrequest=%s""",
                    (datetime.now(), request_id,)
                )
                await conn.commit()
        return "Request is rejected successfully"
    except Exception as e:
        return f"Error: {e}"


async def get_student_requests(student_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT er.idrequest, c.course_name, c.course_code, er.status, er.requested_at, er.reviewed_at
                FROM enrollment_request er
                JOIN course c ON er.idcourse = c.idcourse
                WHERE er.idstudent = %s
                ORDER BY er.requested_at DESC""",
                (student_id,)
            )
            result = await cur.fetchall()
    return result if result else []


async def update_teacher_password(teacher_id: int, new_hash: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "UPDATE teacher SET password_hash = %s WHERE idteacher = %s",
                    (new_hash, teacher_id)
                )
                await conn.commit()
        return "Password updated successfully"
    except Exception as e:
        return f"Error: {e}"


async def update_student_password(student_id: int, new_hash: str):
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "UPDATE student SET password_hash = %s WHERE idstudent = %s",
                    (new_hash, student_id)
                )
                await conn.commit()
        return "Password updated successfully"
    except Exception as e:
        return f"Error: {e}"

async def get_all_projects_with_requirements():
    """Get all projects with their required course IDs."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT idproject, project_name, description FROM project")
            projects = await cur.fetchall()
            
            for project in projects:
                await cur.execute(
                    "SELECT idcourse FROM project_requirement WHERE idproject = %s",
                    (project["idproject"],)
                )
                reqs = await cur.fetchall()
                project["required_courses"] = [r["idcourse"] for r in reqs]
    
    return list(projects) if projects else []

async def search_students_by_name(query:str):
    pool = await get_pool()
    search = f"%{query.strip()}%"
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT idstudent, fname,lname, student_number FROM student
                WHERE fname LIKE %s
                OR lname LIKE %s
                OR CONCAT(fname, ' ', lname) LIKE %s
                OR student_number LIKE %s
                ORDER BY lname, fname
                LIMIT 10""",
                (search,search,search,search)
            )
            result = await cur.fetchall()
    return result if result else[]

async def get_all_teachers():
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT idteacher,fname,lname,email FROM teacher")
            result = await cur.fetchall()
    return list(result) if result else []

async def get_project_requirements_for_course(course_name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT idproject FROM project WHERE project_name = %s",
                (course_name,)
            )
            project = await cur.fetchone()
            
            if not project:
                return []
            
            await cur.execute(
                """SELECT pr.idcourse, c.course_name, c.course_code 
                   FROM project_requirement pr
                   JOIN course c ON pr.idcourse = c.idcourse
                   WHERE pr.idproject = %s""",
                (project["idproject"],)
            )
            result = await cur.fetchall()
    
    return list(result) if result else []

async def search_courses_by_name(query: str):
    pool = await get_pool()
    search = f"%{query.strip()}%"
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT idcourse, course_code, course_name, credit, category
                   FROM course
                   WHERE course_name LIKE %s
                      OR course_code LIKE %s
                   ORDER BY course_name
                   LIMIT 10""",
                (search, search)
            )
            result = await cur.fetchall()
    return list(result) if result else []

async def get_group_stats_for_student(student_id:int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT idgroup FROM student_group
                WHERE idstudent=%s LIMIT 1""",
            (student_id,)
            )
            group = await cur.fetchone()
            if not group:
                return None
            
            group_id = group["idgroup"]

            await cur.execute(
                """SELECT idstudent FROM student_group
                WHERE idgroup=%s""",
                (group_id,)
            )
            members = await cur.fetchall()

            all_credits = []
            for member in members:
                await cur.execute(
                    """SELECT COALESCE(SUM(c.credit), 0) as credits
                       FROM enrollment e
                       JOIN course c ON e.idcourse = c.idcourse
                       WHERE e.idstudent = %s AND e.status = 'completed'""",
                    (member["idstudent"],)
                )
                result = await cur.fetchone()
                all_credits.append(int(result["credits"]))
    
    return {
        "avg_credits": round(sum(all_credits) / len(all_credits)) if all_credits else 0,
        "max_credits": max(all_credits) if all_credits else 0,
        "group_size": len(members)
    }

async def save_telegram_session(chat_id: str, user_role: str, user_id: int, user_name: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO telegram_sessions (chat_id, user_role, user_id, user_name)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE 
                   user_role=%s, user_id=%s, user_name=%s, logged_in_at=NOW()""",
                (chat_id, user_role, user_id, user_name, user_role, user_id, user_name)
            )
            await conn.commit()

async def get_telegram_session(chat_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM telegram_sessions WHERE chat_id = %s",
                (chat_id,)
            )
            return await cur.fetchone()

async def delete_telegram_session(chat_id: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM telegram_sessions WHERE chat_id = %s",
                (chat_id,)
            )
            await conn.commit()