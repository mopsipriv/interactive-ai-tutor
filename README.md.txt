## Database Setup

### Requirements
- MySQL 8.0+
- MySQL Workbench

### How to run

1. Open MySQL Workbench
2. Connect to local instance
3. Open SQL editor (Ctrl+T)
4. Open file: peppi_db.sql
5. Execute all (Ctrl+Shift+Enter)
6. Refresh schemas — mydb should appear

### Schema overview
- teacher — sends and receives bot queries
- student — belongs to group_cohort
- course — has credits and category
- enrollment — student course history with grades
- project — has requirements (courses needed)
- project_requirement — which courses needed per project
- project_group — students who passed eligibility check
- group_cohort — student group tied to teacher
- student_group — student ↔ group mapping
- teacher_query_log — bot query history

### Test eligibility query
SELECT 
    s.fname, s.lname, c.course_name,
    CASE WHEN e.status = 'completed' 
         THEN 'done' ELSE 'missing' 
    END AS eligibility
FROM project_requirement pr
JOIN course c ON pr.idcourse = c.idcourse
LEFT JOIN enrollment e 
    ON e.idcourse = pr.idcourse 
    AND e.idstudent = 1
JOIN student s ON s.idstudent = 1
WHERE pr.idproject = 1;