CREATE DATABASE IF NOT EXISTS peppi_db;
USE peppi_db;
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS student (
    idstudent INT AUTO_INCREMENT PRIMARY KEY,
    student_number VARCHAR(20) NOT NULL,
    fname VARCHAR(30) NOT NULL,
    lname VARCHAR(30) NOT NULL,
    email VARCHAR(60) NOT NULL,
    study_right VARCHAR(60) NOT NULL,
    valid_from DATE NOT NULL,
    valid_until DATE NOT NULL,
    password_hash VARCHAR(255) DEFAULT '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'
);

INSERT INTO student (student_number, fname, lname, email, study_right, valid_from, valid_until, password_hash) VALUES
('H100001', 'John', 'Smith', 'john.smith@example.com', 'Information Technology', '2024-09-01', '2028-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100002', 'Emma', 'Johnson', 'emma.johnson@example.com', 'Business Administration', '2024-09-01', '2028-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100003', 'Liam', 'Brown', 'liam.brown@example.com', 'Computer Science', '2023-09-01', '2027-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100004', 'Olivia', 'Davis', 'olivia.davis@example.com', 'Engineering', '2024-09-01', '2028-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100005', 'Noah', 'Miller', 'noah.miller@example.com', 'Information Technology', '2023-09-01', '2027-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100006', 'Ava', 'Wilson', 'ava.wilson@example.com', 'Business Administration', '2024-09-01', '2028-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100007', 'Ethan', 'Moore', 'ethan.moore@example.com', 'Data Science', '2024-09-01', '2028-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100008', 'Sophia', 'Taylor', 'sophia.taylor@example.com', 'Computer Science', '2023-09-01', '2027-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100009', 'Mason', 'Anderson', 'mason.anderson@example.com', 'Engineering', '2024-09-01', '2028-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('H100010', 'Isabella', 'Thomas', 'isabella.thomas@example.com', 'Data Science', '2024-09-01', '2028-06-30', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC');


CREATE TABLE IF NOT EXISTS teacher (
    idteacher INT AUTO_INCREMENT PRIMARY KEY,
    fname VARCHAR(30) NOT NULL,
    lname VARCHAR(30) NOT NULL,
    email VARCHAR(60) NOT NULL,
    password_hash VARCHAR(255) DEFAULT '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'
);

INSERT INTO teacher (fname, lname, email, password_hash) VALUES
('James', 'White', 'james.white@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Charlotte', 'Harris', 'charlotte.harris@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Benjamin', 'Martin', 'benjamin.martin@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Amelia', 'Clark', 'amelia.clark@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Lucas', 'Rodriguez', 'lucas.rodriguez@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Harper', 'Lewis', 'harper.lewis@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Henry', 'Lee', 'henry.lee@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Evelyn', 'Walker', 'evelyn.walker@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Alexander', 'Hall', 'alexander.hall@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'),
('Mia', 'Allen', 'mia.allen@example.com', '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC');


CREATE TABLE IF NOT EXISTS course (
    idcourse INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    credit INT NOT NULL,
    category VARCHAR(30)
);

INSERT INTO course (course_code, course_name, credit, category) VALUES

('TVT1001', 'Matematiikan perusteet tietotekniikassa 1', 3, 'perus'),
('TVT1002', 'Digitaalitekniikan perusteet tietotekniikassa', 3, 'perus'),
('TVT1003', 'Johdatus ohjelmointiin', 5, 'perus'),
('TVT1004', 'Ohjelmointi 1', 5, 'perus'),
('TVT1005', 'Ohjelmointi 2', 5, 'perus'),
('TVT1006', 'Tietokannat', 5, 'perus'),
('TVT1007', 'Web-ohjelmointi', 5, 'perus'),
('TVT1011', 'Tietoliikenteen perusteet', 3, 'perus'),
('TVT1012', 'Käyttöjärjestelmät', 3, 'perus'),
('TVT1013', 'Linux-käyttöjärjestelmät', 3, 'perus'),


('TVT2001', 'Tekoälyn ohjelmointi', 5, 'ammatti'),
('TVT2002', 'Koneoppiminen', 5, 'ammatti'),
('TVT2003', 'Python-ohjelmointi', 3, 'ammatti'),
('TVT2006', 'Ohjelmistotuotanto', 5, 'ammatti'),
('TVT2007', 'Mobiiliohjelmointi', 5, 'ammatti'),
('TVT2008', 'Pilvipalvelut ja DevOps', 5, 'ammatti'),
('TVT2009', 'Tietoturvan perusteet', 3, 'ammatti'),
('TVT2010', 'Käyttöliittymäsuunnittelu', 3, 'ammatti'),


('TVT3001', 'Harjoittelu', 30, 'harjoittelu'),
('TVT3002', 'Opinnäytetyö', 15, 'opinnäyte');


CREATE TABLE IF NOT EXISTS group_cohort (
    idgroup_cohort INT AUTO_INCREMENT PRIMARY KEY,
    group_code VARCHAR(20) NOT NULL,
    idteacher INT,
    FOREIGN KEY (idteacher) REFERENCES teacher(idteacher)
);

INSERT INTO group_cohort (group_code, idteacher) VALUES
('TVT24SPO', 1),
('AVOVAY25S', 2);


CREATE TABLE IF NOT EXISTS enrollment (
    idenrollment INT AUTO_INCREMENT PRIMARY KEY,
    idstudent INT NOT NULL,
    idcourse INT NOT NULL,
    idgroup INT,
    grade INT,
    status VARCHAR(20) NOT NULL DEFAULT 'planned',
    completed_date DATE,
    FOREIGN KEY (idstudent) REFERENCES student(idstudent),
    FOREIGN KEY (idcourse) REFERENCES course(idcourse)
);

INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date) VALUES
(1, 3, 1, 4, 'completed', '2024-12-15'),
(1, 6, 1, 5, 'completed', '2024-12-20'),
(1, 11, 1, NULL, 'ongoing', NULL),
(2, 3, 1, 5, 'completed', '2024-12-15'),
(2, 6, 1, 4, 'completed', '2024-12-20'),
(2, 11, 1, 3, 'completed', '2025-01-10'),
(3, 3, 1, 3, 'completed', '2024-12-15'),
(3, 4, 1, NULL, 'ongoing', NULL),
(4, 3, 1, 2, 'completed', '2024-12-15'),
(5, 3, 2, NULL, 'planned', NULL);


CREATE TABLE IF NOT EXISTS student_group (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idstudent INT NOT NULL,
    idgroup INT NOT NULL,
    FOREIGN KEY (idstudent) REFERENCES student(idstudent),
    FOREIGN KEY (idgroup) REFERENCES group_cohort(idgroup_cohort)
);

INSERT INTO student_group (idstudent, idgroup) VALUES
(1, 1), (2, 1), (3, 1), (4, 1), (1, 2), (5, 2);


CREATE TABLE IF NOT EXISTS project (
    idproject INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    description TEXT
);

INSERT INTO project (project_name, description) VALUES
('AI Chatbot Development', 'Tekoälypohjainen chatbot-projekti opettajien tueksi'),
('Web Application Project', 'Full-stack web-sovelluksen kehitysprojekti');


CREATE TABLE IF NOT EXISTS project_group (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idproject INT NOT NULL,
    idstudent INT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (idproject) REFERENCES project(idproject),
    FOREIGN KEY (idstudent) REFERENCES student(idstudent)
);

INSERT INTO project_group (idproject, idstudent, status) VALUES
(1, 2, 'active');


CREATE TABLE IF NOT EXISTS project_requirement (
    id INT AUTO_INCREMENT PRIMARY KEY,
    idproject INT NOT NULL,
    idcourse INT NOT NULL,
    FOREIGN KEY (idproject) REFERENCES project(idproject),
    FOREIGN KEY (idcourse) REFERENCES course(idcourse)
);

INSERT INTO project_requirement (idproject, idcourse) VALUES
(1, 3), (2, 3), (2, 4), (1, 6), (2, 7), (1, 11);


CREATE TABLE IF NOT EXISTS teacher_query_log (
    idlog INT AUTO_INCREMENT PRIMARY KEY,
    idteacher INT NOT NULL,
    query_text TEXT,
    intent VARCHAR(50),
    result TEXT,
    created_at DATETIME,
    FOREIGN KEY (idteacher) REFERENCES teacher(idteacher)
);


CREATE TABLE IF NOT EXISTS curriculum (
    id INT AUTO_INCREMENT PRIMARY KEY,
    program_code VARCHAR(20),
    program_name VARCHAR(100),
    semester INT,
    idcourse INT,
    course_type VARCHAR(20),
    FOREIGN KEY (idcourse) REFERENCES course(idcourse)
);

INSERT INTO curriculum (program_code, program_name, semester, idcourse, course_type) VALUES
('TVT', 'Tietotekniikka', 1, 1, 'mandatory'),
('TVT', 'Tietotekniikka', 1, 2, 'mandatory'),
('TVT', 'Tietotekniikka', 1, 3, 'mandatory'),
('TVT', 'Tietotekniikka', 2, 4, 'mandatory'),
('TVT', 'Tietotekniikka', 2, 6, 'mandatory'),
('TVT', 'Tietotekniikka', 3, 5, 'mandatory'),
('TVT', 'Tietotekniikka', 3, 7, 'elective'),
('TVT', 'Tietotekniikka', 4, 11, 'mandatory');

CREATE TABLE IF NOT EXISTS enrollment_request (
    idrequest INT AUTO_INCREMENT PRIMARY KEY,
    idstudent INT NOT NULL,
    idcourse INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    requested_at DATETIME,
    reviewed_at DATETIME,
    FOREIGN KEY (idstudent) REFERENCES student(idstudent),
    FOREIGN KEY (idcourse) REFERENCES course(idcourse)
);