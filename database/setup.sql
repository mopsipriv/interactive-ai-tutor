-- ============================================================
-- peppi_db - AI Tutor Assistant
-- TVT2025S-OHJ (Ohjelmistokehitys) - Real Curriculum
-- Full reset: DROP + CREATE + INSERT
-- ============================================================

DROP DATABASE IF EXISTS peppi_db;
CREATE DATABASE peppi_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE peppi_db;
SET NAMES utf8mb4;

-- ============================================================
-- STUDENT
-- ============================================================
CREATE TABLE student (
    idstudent      INT AUTO_INCREMENT PRIMARY KEY,
    student_number VARCHAR(20)  NOT NULL UNIQUE,
    fname          VARCHAR(30)  NOT NULL,
    lname          VARCHAR(30)  NOT NULL,
    email          VARCHAR(60)  NOT NULL UNIQUE,
    study_right    VARCHAR(60)  NOT NULL DEFAULT 'TVT2025S-OHJ',
    valid_from     DATE         NOT NULL,
    valid_until    DATE         NOT NULL,
    password_hash  VARCHAR(255) NOT NULL DEFAULT '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'
);

INSERT INTO student (student_number, fname, lname, email, study_right, valid_from, valid_until) VALUES
('H100001', 'John',     'Smith',    'john.smith@oamk.fi',     'TVT2025S-OHJ', '2024-09-01', '2028-06-30'),
('H100002', 'Emma',     'Johnson',  'emma.johnson@oamk.fi',   'TVT2025S-OHJ', '2024-09-01', '2028-06-30'),
('H100003', 'Liam',     'Brown',    'liam.brown@oamk.fi',     'TVT2025S-OHJ', '2023-09-01', '2027-06-30'),
('H100004', 'Olivia',   'Davis',    'olivia.davis@oamk.fi',   'TVT2025S-OHJ', '2024-09-01', '2028-06-30'),
('H100005', 'Noah',     'Miller',   'noah.miller@oamk.fi',    'TVT2025S-OHJ', '2023-09-01', '2027-06-30'),
('H100006', 'Ava',      'Wilson',   'ava.wilson@oamk.fi',     'TVT2025S-OHJ', '2024-09-01', '2028-06-30'),
('H100007', 'Ethan',    'Moore',    'ethan.moore@oamk.fi',    'TVT2025S-OHJ', '2024-09-01', '2028-06-30'),
('H100008', 'Sophia',   'Taylor',   'sophia.taylor@oamk.fi',  'TVT2025S-OHJ', '2023-09-01', '2027-06-30'),
('H100009', 'Mason',    'Anderson', 'mason.anderson@oamk.fi', 'TVT2025S-OHJ', '2024-09-01', '2028-06-30'),
('H100010', 'Isabella', 'Thomas',   'isabella.thomas@oamk.fi','TVT2025S-OHJ', '2024-09-01', '2028-06-30');

-- ============================================================
-- TEACHER
-- ============================================================
CREATE TABLE teacher (
    idteacher     INT AUTO_INCREMENT PRIMARY KEY,
    fname         VARCHAR(30)  NOT NULL,
    lname         VARCHAR(30)  NOT NULL,
    email         VARCHAR(60)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL DEFAULT '$2b$12$g2CjXUr57vOVw/b6wViiOuAW1mbvJLXX9Gh2Y0LSP5ud.AVnnHSyC'
);

INSERT INTO teacher (fname, lname, email) VALUES
('James',     'White',     'james.white@oamk.fi'),
('Charlotte', 'Harris',    'charlotte.harris@oamk.fi'),
('Benjamin',  'Martin',    'benjamin.martin@oamk.fi'),
('Amelia',    'Clark',     'amelia.clark@oamk.fi'),
('Lucas',     'Rodriguez', 'lucas.rodriguez@oamk.fi'),
('Harper',    'Lewis',     'harper.lewis@oamk.fi'),
('Henry',     'Lee',       'henry.lee@oamk.fi'),
('Evelyn',    'Walker',    'evelyn.walker@oamk.fi'),
('Alexander', 'Hall',      'alexander.hall@oamk.fi'),
('Mia',       'Allen',     'mia.allen@oamk.fi');

-- ============================================================
-- COURSE
-- Real courses from TVT2025S-OHJ curriculum
-- year_of_study: 1-4
-- category: perus / ammatti / projekti / harjoittelu / opinnäyte / vapaa
-- ============================================================
CREATE TABLE course (
    idcourse       INT AUTO_INCREMENT PRIMARY KEY,
    course_code    VARCHAR(20)  NOT NULL UNIQUE,
    course_name    VARCHAR(120) NOT NULL,
    credit         INT          NOT NULL,
    category       VARCHAR(30)  NOT NULL,
    year_of_study  INT          NOT NULL DEFAULT 1
);

INSERT INTO course (course_code, course_name, credit, category, year_of_study) VALUES
-- ── Year 1 ──────────────────────────────────────────────────
('IN00EH18', 'Matematiikan perusteet tietotekniikassa 1',        3,  'perus',      1),
('IN00EH20', 'Digitaalitekniikan perusteet tietotekniikassa',     3,  'perus',      1),
('IN00CS84', 'Johdatus ohjelmointiin',                           5,  'perus',      1),
('YY00DU47', 'Digi- ja tietotekniset taidot',                    3,  'perus',      1),
('YY00DU46', 'Ammatillinen kehittyminen ja työelämätaidot',       5,  'perus',      1),
('IN00CS82', 'Sähköturvallisuus ja elektroniikan perusteet',      5,  'perus',      1),
('YY00DU50', 'Työelämän viestintätaidot',                        3,  'perus',      1),
('IN00EP47', 'Tietotekniikan sovellusprojekti',                   9,  'projekti',   1),
('IN00EP46', 'Vektorit ja kompleksiluvut',                        3,  'perus',      1),
('IN00EH21', 'Matematiikan perusteet tietotekniikassa 2',         3,  'perus',      1),
('IN00DL11', 'Tietokannat ja rajapinnat',                        5,  'perus',      1),
('IN00CS88', 'Olio-ohjelmointi ja oliopohjainen suunnittelu',     5,  'perus',      1),
('IN00ED14', 'Ohjelmistokehityksen sovellusprojekti',            15,  'projekti',   1),

-- ── Year 2 ──────────────────────────────────────────────────
('IN00DL12', 'Web-sovellusten perusteet',                        5,  'ammatti',    2),
('IN00CT04', 'Pilvipalvelut',                                     5,  'ammatti',    2),
('IN00FB05', 'Ohjelmistotestaus',                                5,  'ammatti',    2),
('YY00DU52', 'English for Working Life',                         3,  'perus',      2),
('IN00ED15', 'Web-ohjelmoinnin sovellusprojekti',               15,  'projekti',   2),
('IN00EH22', 'Fysiikan perusteet tietotekniikassa',              3,  'perus',      2),
('IN00CT07', 'Mobiiliohjelmointi natiiviteknologioilla',          5,  'ammatti',    2),
('IN00CT08', 'Web- ja hybriditeknologiat mobiiliohjelmoinnissa',  5,  'ammatti',    2),
('IN00ED17', 'Mobiilikehitysprojekti',                          15,  'projekti',   2),

-- ── Year 3 ──────────────────────────────────────────────────
('IN00DU04', 'Linux Administration',                             5,  'ammatti',    3),
('IN00CT12', 'Advanced Software Development Techniques',         5,  'ammatti',    3),
('IN00ED20', 'Components of IoT Application',                    5,  'ammatti',    3),
('IN00CT09', 'Soveltava matematiikka ja fysiikka ohjelmoinnissa', 5,  'ammatti',    3),
('YY00DU51', 'Svenska för arbetslivet',                          3,  'perus',      3),
('IN00FA96', 'Java-ohjelmointi',                                 3,  'ammatti',    3),
('IN00ED21', 'Yrittäjyys',                                       3,  'ammatti',    3),
('YY00DU53', 'Viestintä tutkimus- ja kehittämistyössä',          3,  'perus',      3),
('IN00CT17', 'Yritys- tai hankelähtöinen tuotekehitysprojekti 1',10, 'projekti',   3),
('IN00FM22', 'Ammattitaidon syventäminen 1',                    10,  'ammatti',    3),

-- ── Year 4 ──────────────────────────────────────────────────
('IN00CT18', 'Yritys- tai hankelähtöinen tuotekehitysprojekti 2',10, 'projekti',   4),
('IN00FM23', 'Ammattitaidon syventäminen 2',                    10,  'ammatti',    4),
('IN00CT02', 'Harjoittelu',                                     30,  'harjoittelu',4),
('T009015',  'Opinnäytetyö',                                    15,  'opinnäyte',  4),

-- ── Vapaasti valittavat ──────────────────────────────────────
('ID00BQ11', 'Product Design and Implementation',               15,  'vapaa',      3);

-- ============================================================
-- GROUP COHORT
-- ============================================================
CREATE TABLE group_cohort (
    idgroup_cohort INT AUTO_INCREMENT PRIMARY KEY,
    group_code     VARCHAR(20) NOT NULL UNIQUE,
    idteacher      INT,
    FOREIGN KEY (idteacher) REFERENCES teacher(idteacher)
);

INSERT INTO group_cohort (group_code, idteacher) VALUES
('TVT24SPO',   1),
('TVT25SPO',   2),
('AVOVAY25S',  3);

-- ============================================================
-- STUDENT GROUP
-- ============================================================
CREATE TABLE student_group (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    idstudent  INT NOT NULL,
    idgroup    INT NOT NULL,
    FOREIGN KEY (idstudent) REFERENCES student(idstudent),
    FOREIGN KEY (idgroup)   REFERENCES group_cohort(idgroup_cohort)
);

INSERT INTO student_group (idstudent, idgroup) VALUES
(1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
(6, 2), (7, 2), (8, 2),
(9, 3), (10, 3);

-- ============================================================
-- CURRICULUM
-- Maps program → year → course (mandatory/elective)
-- ============================================================
CREATE TABLE curriculum (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    program_code VARCHAR(20)  NOT NULL,
    program_name VARCHAR(100) NOT NULL,
    year_of_study INT         NOT NULL,
    idcourse     INT          NOT NULL,
    course_type  VARCHAR(20)  NOT NULL DEFAULT 'mandatory',
    FOREIGN KEY (idcourse) REFERENCES course(idcourse)
);

INSERT INTO curriculum (program_code, program_name, year_of_study, idcourse, course_type) VALUES
-- Year 1
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  1,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  2,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  3,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  4,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  5,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  6,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  7,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  8,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  9,  'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  10, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  11, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  12, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 1,  13, 'mandatory'),
-- Year 2
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  14, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  15, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  16, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  17, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  18, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  19, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  20, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  21, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 2,  22, 'mandatory'),
-- Year 3
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  23, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  24, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  25, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  26, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  27, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  28, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  29, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  30, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  31, 'elective'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  32, 'elective'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 3,  36, 'elective'),
-- Year 4
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 4,  33, 'elective'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 4,  34, 'elective'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 4,  35, 'mandatory'),
('TVT2025S-OHJ', 'Tietotekniikka / Ohjelmistokehitys', 4,  36, 'mandatory');

-- ============================================================
-- ENROLLMENT
-- ============================================================
CREATE TABLE enrollment (
    idenrollment   INT AUTO_INCREMENT PRIMARY KEY,
    idstudent      INT         NOT NULL,
    idcourse       INT         NOT NULL,
    idgroup        INT,
    grade          INT,
    status         VARCHAR(20) NOT NULL DEFAULT 'planned',
    completed_date DATE,
    FOREIGN KEY (idstudent) REFERENCES student(idstudent),
    FOREIGN KEY (idcourse)  REFERENCES course(idcourse)
);

-- John Smith (H100001) — year 1 mostly done, year 2 ongoing
INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date) VALUES
(1,  1,  1, 4, 'completed', '2024-12-10'),
(1,  2,  1, 3, 'completed', '2024-12-10'),
(1,  3,  1, 5, 'completed', '2024-12-15'),
(1,  4,  1, 4, 'completed', '2025-05-20'),
(1,  5,  1, 3, 'completed', '2025-05-20'),
(1,  6,  1, 4, 'completed', '2025-05-15'),
(1,  7,  1, 3, 'completed', '2025-05-20'),
(1,  8,  1, 3, 'completed', '2025-05-25'),
(1, 14,  1, NULL, 'ongoing',  NULL),
(1, 15,  1, NULL, 'ongoing',  NULL);

-- Emma Johnson (H100002) — strong student
INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date) VALUES
(2,  1,  1, 5, 'completed', '2024-12-10'),
(2,  2,  1, 4, 'completed', '2024-12-10'),
(2,  3,  1, 5, 'completed', '2024-12-15'),
(2,  4,  1, 5, 'completed', '2025-05-20'),
(2,  5,  1, 4, 'completed', '2025-05-20'),
(2,  6,  1, 5, 'completed', '2025-05-15'),
(2,  7,  1, 5, 'completed', '2025-05-20'),
(2,  8,  1, 4, 'completed', '2025-05-25'),
(2, 11,  1, 4, 'completed', '2025-01-10'),
(2, 12,  1, 5, 'completed', '2025-01-15'),
(2, 13,  1, 5, 'completed', '2025-05-30'),
(2, 14,  1, NULL, 'ongoing',  NULL);

-- Liam Brown (H100003) — at risk, slow progress
INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date) VALUES
(3,  3,  1, 2, 'completed', '2024-12-15'),
(3,  6,  1, 2, 'completed', '2025-05-15'),
(3,  4,  1, NULL, 'ongoing',  NULL);

-- Olivia Davis (H100004)
INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date) VALUES
(4,  1,  1, 3, 'completed', '2024-12-10'),
(4,  3,  1, 4, 'completed', '2024-12-15'),
(4,  4,  1, 3, 'completed', '2025-05-20'),
(4,  6,  1, 4, 'completed', '2025-05-15'),
(4, 14,  1, NULL, 'planned',  NULL);

-- Noah Miller (H100005)
INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date) VALUES
(5,  3,  1, 3, 'completed', '2024-12-15'),
(5,  4,  1, NULL, 'ongoing',  NULL);

-- ============================================================
-- PROJECT
-- ============================================================
CREATE TABLE project (
    idproject    INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    description  TEXT
);

INSERT INTO project (project_name, description) VALUES
('AI Chatbot Development',   'Tekoälypohjainen chatbot-projekti opettajien ja opiskelijoiden tueksi. Vaatii: Johdatus ohjelmointiin, Tietokannat ja rajapinnat, Linux Administration.'),
('Web Application Project',  'Full-stack web-sovelluksen kehitysprojekti. Vaatii: Johdatus ohjelmointiin, Olio-ohjelmointi, Web-sovellusten perusteet.'),
('Mobile App Project',       'Mobiilisovelluksen kehitys natiiviteknologioilla. Vaatii: Ohjelmointi 1, Mobiiliohjelmointi natiiviteknologioilla.');

-- ============================================================
-- PROJECT REQUIREMENT (prerequisite courses)
-- ============================================================
CREATE TABLE project_requirement (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    idproject INT NOT NULL,
    idcourse  INT NOT NULL,
    FOREIGN KEY (idproject) REFERENCES project(idproject),
    FOREIGN KEY (idcourse)  REFERENCES course(idcourse)
);

INSERT INTO project_requirement (idproject, idcourse) VALUES
-- AI Chatbot: Johdatus ohjelmointiin, Tietokannat ja rajapinnat, Linux Administration
(1,  3), (1, 11), (1, 23),
-- Web App: Johdatus ohjelmointiin, Olio-ohjelmointi, Web-sovellusten perusteet
(2,  3), (2, 12), (2, 14),
-- Mobile: Olio-ohjelmointi, Mobiiliohjelmointi natiiviteknologioilla
(3, 12), (3, 20);

-- ============================================================
-- PROJECT GROUP (students in projects)
-- ============================================================
CREATE TABLE project_group (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    idproject INT NOT NULL,
    idstudent INT NOT NULL,
    status    VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (idproject) REFERENCES project(idproject),
    FOREIGN KEY (idstudent) REFERENCES student(idstudent)
);

INSERT INTO project_group (idproject, idstudent, status) VALUES
(1, 2, 'active'),
(2, 1, 'active'),
(2, 4, 'active');

-- ============================================================
-- ENROLLMENT REQUEST
-- ============================================================
CREATE TABLE enrollment_request (
    idrequest    INT AUTO_INCREMENT PRIMARY KEY,
    idstudent    INT         NOT NULL,
    idcourse     INT         NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending',
    requested_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at  DATETIME,
    FOREIGN KEY (idstudent) REFERENCES student(idstudent),
    FOREIGN KEY (idcourse)  REFERENCES course(idcourse)
);

-- ============================================================
-- TEACHER QUERY LOG
-- ============================================================
CREATE TABLE teacher_query_log (
    idlog      INT AUTO_INCREMENT PRIMARY KEY,
    idteacher  INT      NOT NULL,
    query_text TEXT,
    intent     VARCHAR(50),
    result     TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idteacher) REFERENCES teacher(idteacher)
);

-- ============================================================
-- VERIFY
-- ============================================================
SELECT 'Students:' AS tbl, COUNT(*) AS cnt FROM student
UNION ALL SELECT 'Teachers:',  COUNT(*) FROM teacher
UNION ALL SELECT 'Courses:',   COUNT(*) FROM course
UNION ALL SELECT 'Curriculum:',COUNT(*) FROM curriculum
UNION ALL SELECT 'Enrollments:',COUNT(*) FROM enrollment;

-- ============================================================
-- DIN2025S - Degree Programme in Information Technology (English)
-- New courses only (shared courses already exist above)
-- ============================================================

INSERT INTO course (course_code, course_name, credit, category, year_of_study) VALUES
-- ── Year 1 (DIN) ────────────────────────────────────────────
('ID00EK08', 'Mathematics for Programmers',                      5,  'perus',    1),
('ID00CS34', 'Introduction to Programming and Software Dev',     5,  'perus',    1),
('ID00CS37', 'Computer Devices and Operating Systems',           5,  'perus',    1),
('ID00CS38', 'HTML and CSS Programming',                         5,  'perus',    1),
('ID00DH72', 'Internet Programming and Databases',               5,  'perus',    1),
('ID00CS41', 'Object Oriented Browser Programming',              5,  'perus',    1),
('ID00EK07', 'Physics for Programmers',                          5,  'perus',    1),
('ID00DW07', 'Web Programming Project',                         15,  'projekti', 1),
('YY00DU55', 'Finnish Language 1: Survive!',                     3,  'kieli',    1),
('YY00DU56', 'Finnish Language 2: Move on!',                     3,  'kieli',    1),
('YY00DU57', 'Finnish Language 3: Speak!',                       3,  'kieli',    1),

-- ── Year 2 (DIN) ────────────────────────────────────────────
('ID00CS44', 'Web Development Frameworks',                       5,  'ammatti',  2),
('ID00CS45', 'Cloud Services',                                   5,  'ammatti',  2),
('ID00ER99', 'Software Testing',                                 5,  'ammatti',  2),
('ID00CS47', 'Advanced Web Applications Project',               15,  'projekti', 2),
('ID00CS48', 'Mobile Programming with Native Technologies',      5,  'ammatti',  2),
('ID00CS49', 'Web- and Hybrid Technologies in Mobile Prog',      5,  'ammatti',  2),
('ID00CS50', 'Applied Mathematics and Physics in Programming',   5,  'ammatti',  2),
('ID00ES00', 'Mobile Development Project',                      12,  'projekti', 2),
('YY00ED71', 'Taitavaksi kokousviestijäksi',                     3,  'kieli',    2),
('YY00DU58', 'Finnish Language 4: Write!',                       3,  'kieli',    2),
('YY00EJ16', 'Finnish Language 5: Everyday Life',                4,  'kieli',    2),

-- ── Year 3 (DIN) ────────────────────────────────────────────
('ID00DU06', 'Advanced Software Development Techniques',         5,  'ammatti',  3),
('ID00CS53', 'Components of IoT Application',                    5,  'ammatti',  3),
('ID00CS54', 'Data Storage and Data Analysis',                   5,  'ammatti',  3),
('YY00DV86', 'English Communication in Research and Dev',        3,  'perus',    3),
('T771010D', 'Company-Oriented Product Development Project 1',  10,  'projekti', 3),
('ID00ES01', 'Entrepreneurship',                                 5,  'ammatti',  3),
('ID00CS46', 'Java Programming',                                 5,  'ammatti',  3),
('ID00EO11', 'Deepening of Student\'s Professional Skills',     10,  'ammatti',  3),
('YY00EJ17', 'Finnish Language 6: Finnish Culture',              4,  'kieli',    3),
('YY00EJ18', 'Finnish Language 7: Working Life',                 4,  'kieli',    3),

-- ── Year 4 (DIN) ────────────────────────────────────────────
('T772010D', 'Company-Oriented Product Development Project 2',  10,  'projekti', 4),
('T008130D', 'Harjoittelu',                                     30,  'harjoittelu', 4),
('T009015D', 'Opinnäytetyö',                                    15,  'opinnäyte', 4);

-- ── Group for DIN program ────────────────────────────────────
INSERT INTO group_cohort (group_code, idteacher) VALUES
('DIN25SPO', 4);

-- ── DIN students (H200001-H200005) ──────────────────────────
INSERT INTO student (student_number, fname, lname, email, study_right, valid_from, valid_until) VALUES
('H200001', 'Alice',   'Korhonen',  'alice.korhonen@oamk.fi',  'DIN2025S', '2025-09-01', '2029-06-30'),
('H200002', 'Carlos',  'Virtanen',  'carlos.virtanen@oamk.fi', 'DIN2025S', '2025-09-01', '2029-06-30'),
('H200003', 'Yuki',    'Mäkinen',   'yuki.makinen@oamk.fi',    'DIN2025S', '2025-09-01', '2029-06-30'),
('H200004', 'Daniel',  'Leinonen',  'daniel.leinonen@oamk.fi', 'DIN2025S', '2025-09-01', '2029-06-30'),
('H200005', 'Priya',   'Nieminen',  'priya.nieminen@oamk.fi',  'DIN2025S', '2025-09-01', '2029-06-30');

-- ── Assign DIN students to group ────────────────────────────
-- group_cohort id for DIN25SPO will be 4
INSERT INTO student_group (idstudent, idgroup) VALUES
(11, 4), (12, 4), (13, 4), (14, 4), (15, 4);

-- ── Curriculum for DIN2025S ─────────────────────────────────
-- Shared courses reuse their existing idcourse
-- We reference by course_code in a subquery pattern via VALUES with known IDs
-- TVT shared: YY00DU46=5, YY00DU47=4, YY00DU52=17, IN00FM22=32, IN00FM23=34

INSERT INTO curriculum (program_code, program_name, year_of_study, idcourse, course_type)
SELECT 'DIN2025S', 'Degree Programme in Information Technology', 1, idcourse, 'mandatory'
FROM course WHERE course_code IN ('ID00EK08','ID00CS34','YY00DU46','YY00DU47','YY00DU52',
    'ID00CS37','ID00CS38','ID00DH72','ID00CS41','ID00EK07','ID00DW07',
    'YY00DU55','YY00DU56','YY00DU57','YY00DU50');

INSERT INTO curriculum (program_code, program_name, year_of_study, idcourse, course_type)
SELECT 'DIN2025S', 'Degree Programme in Information Technology', 2, idcourse, 'mandatory'
FROM course WHERE course_code IN ('ID00CS44','ID00CS45','ID00ER99','ID00CS47',
    'ID00CS48','ID00CS49','ID00CS50','ID00ES00',
    'YY00ED71','YY00DU51','YY00DU58','YY00EJ16');

INSERT INTO curriculum (program_code, program_name, year_of_study, idcourse, course_type)
SELECT 'DIN2025S', 'Degree Programme in Information Technology', 3, idcourse, 'mandatory'
FROM course WHERE course_code IN ('ID00DU06','ID00CS53','ID00CS54','YY00DV86','T771010D');

INSERT INTO curriculum (program_code, program_name, year_of_study, idcourse, course_type)
SELECT 'DIN2025S', 'Degree Programme in Information Technology', 3, idcourse, 'elective'
FROM course WHERE course_code IN ('IN00FM22','ID00ES01','ID00CS46','ID00EO11',
    'YY00EJ17','YY00EJ18');

INSERT INTO curriculum (program_code, program_name, year_of_study, idcourse, course_type)
SELECT 'DIN2025S', 'Degree Programme in Information Technology', 4, idcourse, 'mandatory'
FROM course WHERE course_code IN ('T008130D','T009015D');

INSERT INTO curriculum (program_code, program_name, year_of_study, idcourse, course_type)
SELECT 'DIN2025S', 'Degree Programme in Information Technology', 4, idcourse, 'elective'
FROM course WHERE course_code IN ('T772010D','IN00FM23');

-- ── Sample enrollments for DIN students ─────────────────────
INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date)
SELECT 11, idcourse, 4, 4, 'completed', '2025-12-15'
FROM course WHERE course_code IN ('ID00EK08','ID00CS34','ID00CS38');

INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date)
SELECT 12, idcourse, 4, 5, 'completed', '2025-12-15'
FROM course WHERE course_code IN ('ID00EK08','ID00CS34','ID00DH72','ID00CS41');

INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date)
SELECT 13, idcourse, 4, 3, 'completed', '2025-12-15'
FROM course WHERE course_code IN ('ID00CS34');

INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date)
SELECT 11, idcourse, 4, NULL, 'ongoing', NULL
FROM course WHERE course_code = 'ID00CS41';

INSERT INTO enrollment (idstudent, idcourse, idgroup, grade, status, completed_date)
SELECT 12, idcourse, 4, NULL, 'ongoing', NULL
FROM course WHERE course_code = 'ID00CS47';

-- ── Final verify ─────────────────────────────────────────────
SELECT 'Students:'   AS tbl, COUNT(*) AS cnt FROM student
UNION ALL SELECT 'Teachers:',   COUNT(*) FROM teacher
UNION ALL SELECT 'Courses:',    COUNT(*) FROM course
UNION ALL SELECT 'Curriculum:', COUNT(*) FROM curriculum
UNION ALL SELECT 'Groups:',     COUNT(*) FROM group_cohort
UNION ALL SELECT 'Enrollments:',COUNT(*) FROM enrollment;