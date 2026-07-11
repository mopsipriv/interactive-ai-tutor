import asyncio

FAKE_STUDENTS = {
    1: {"idstudent": 1,"student_number": "H123456", "fname": "Aleksandr", "lname":"Starchenkov", "email": "aleksandr.starchenkov@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31"},
    2: {"idstudent": 2,"student_number": "H234567", "fname": "Anna", "lname":"Mäkinen", "email": "anna.makinen@tuni.fi","study_right": "Insinööri (AMK), tietotekniikka" , "valid_from":"2024-08-01","valid_until":"2028-07-31"}
}

FAKE_COURSES = {
    1: {"idcourse":1, "course_code": "TVT1001", "course_name": "Matematiikan perusteet tietotekniikassa 1", "credit":3,"category":"perus"},
    2: {"idcourse":2, "course_code": "TVT1002", "course_name": "Digitaalitekniikan perusteet tietotekniikassa", "credit":3,"category":"perus"}

}

FAKE_ENROLLMENTS = {
    1: {"idenrollment":1,"idstudent": 1,"idcourse": 3,"idgroup":1,"grade":4,"status":"completed","completed_date":"2024-12-15"},
    2: {"idenrollment":10,"idstudent": 5,"idcourse": 3,"idgroup":2,"grade":"NULL","status":"planned","completed_date":"NULL"},
}
async def get_student_from_db(student_id: int):
    await asyncio.sleep(1)

    if student_id in FAKE_STUDENTS:
        return FAKE_STUDENTS[student_id]
    
    return "Not found"

async def get_courses_from_db(course_id: int):
    await asyncio.sleep(1)

    if course_id in FAKE_COURSES:
        return FAKE_COURSES[course_id]
    
    return "Not found"

async def get_student_enrollments(student_id: int):
    await asyncio.sleep(0.5)
    
    student_courses = []
    for enrollment in FAKE_ENROLLMENTS.values():
        if enrollment["idstudent"] == student_id:
            student_courses.append(enrollment)
            
    return student_courses