CREATE DATABASE  IF NOT EXISTS `mydb` /*!40100 DEFAULT CHARACTER SET utf8mb3 */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `mydb`;
-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: mydb
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `course`
--

DROP TABLE IF EXISTS `course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course` (
  `idcourse` int NOT NULL AUTO_INCREMENT,
  `course_code` varchar(20) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `credit` int NOT NULL,
  `category` varchar(60) NOT NULL,
  PRIMARY KEY (`idcourse`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course`
--

LOCK TABLES `course` WRITE;
/*!40000 ALTER TABLE `course` DISABLE KEYS */;
INSERT INTO `course` VALUES (1,'TVT1001','Matematiikan perusteet tietotekniikassa 1',3,'perus'),
(2,'TVT1002','Digitaalitekniikan perusteet tietotekniikassa',3,'perus'),
(3,'TVT1003','Johdatus ohjelmointiin',5,'perus'),
(4,'TVT1004','Ohjelmointi 1',5,'perus'),
(5,'TVT1005','Ohjelmointi 2',5,'perus'),
(6,'TVT1006','Tietokannat',5,'perus'),
(7,'TVT1007','Web-ohjelmointi',5,'perus'),
(8,'TVT2001','Tekoälyn ohjelmointi',5,'ammatti'),
(9,'TVT2002','Koneoppiminen',5,'ammatti'),
(10,'TVT2003','Python-ohjelmointi',3,'ammatti'),
(11,'TVT2004','Tietoliikenteen perusteet',3,'perus'),
(12,'TVT2005','Käyttöjärjestelmät',3,'perus');
/*!40000 ALTER TABLE `course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `enrollment`
--

DROP TABLE IF EXISTS `enrollment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enrollment` (
  `idenrollment` int NOT NULL AUTO_INCREMENT,
  `idstudent` int DEFAULT NULL,
  `idcourse` int DEFAULT NULL,
  `idgroup` int DEFAULT NULL,
  `grade` int DEFAULT NULL,
  `status` enum('completed','ongoing','planned') NOT NULL,
  `completed_date` date DEFAULT NULL,
  PRIMARY KEY (`idenrollment`),
  KEY `fk_enrollment_course_idx` (`idcourse`),
  KEY `fk_enrollment_student_idx` (`idstudent`),
  KEY `fk_enrollment_group` (`idgroup`),
  CONSTRAINT `fk_enrollment_course` FOREIGN KEY (`idcourse`) REFERENCES `course` (`idcourse`),
  CONSTRAINT `fk_enrollment_group` FOREIGN KEY (`idgroup`) REFERENCES `group_cohort` (`idgroup_cohort`),
  CONSTRAINT `fk_enrollment_student` FOREIGN KEY (`idstudent`) REFERENCES `student` (`idstudent`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `enrollment`
--

LOCK TABLES `enrollment` WRITE;
/*!40000 ALTER TABLE `enrollment` DISABLE KEYS */;
INSERT INTO `enrollment` VALUES (1,1,3,1,4,'completed','2024-12-15'),
(2,1,6,1,5,'completed','2024-12-20'),
(3,1,8,1,NULL,'ongoing',NULL),
(4,2,3,1,5,'completed','2024-12-15'),
(5,2,6,1,4,'completed','2024-12-20'),
(6,2,8,1,3,'completed','2025-01-10'),
(7,3,3,1,3,'completed','2024-12-15'),
(8,3,4,1,NULL,'ongoing',NULL),
(9,4,3,1,2,'completed','2024-12-15'),
(10,5,3,2,NULL,'planned',NULL);
/*!40000 ALTER TABLE `enrollment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `group_cohort`
--

DROP TABLE IF EXISTS `group_cohort`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `group_cohort` (
  `idgroup_cohort` int NOT NULL AUTO_INCREMENT,
  `group_code` varchar(20) NOT NULL DEFAULT 'TVT---',
  `idteacher` int DEFAULT NULL,
  PRIMARY KEY (`idgroup_cohort`),
  KEY `fk_group_cohort_teacher_idx` (`idteacher`),
  CONSTRAINT `fk_group_cohort_teacher` FOREIGN KEY (`idteacher`) REFERENCES `teacher` (`idteacher`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `group_cohort`
--

LOCK TABLES `group_cohort` WRITE;
/*!40000 ALTER TABLE `group_cohort` DISABLE KEYS */;
INSERT INTO `group_cohort` VALUES (1,'TVT24SPO',1),(2,'AVOVAY25S',2);
/*!40000 ALTER TABLE `group_cohort` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project` (
  `idproject` int NOT NULL AUTO_INCREMENT,
  `project_name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  PRIMARY KEY (`idproject`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project`
--

LOCK TABLES `project` WRITE;
/*!40000 ALTER TABLE `project` DISABLE KEYS */;
INSERT INTO `project` VALUES (1,'AI Chatbot Development','Tekoälypohjainen chatbot-projekti opettajien tueksi'),
(2,'Web Application Project','Full-stack web-sovelluksen kehitysprojekti');
/*!40000 ALTER TABLE `project` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_group`
--

DROP TABLE IF EXISTS `project_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_group` (
  `idproject_group` int NOT NULL AUTO_INCREMENT,
  `idproject` int NOT NULL,
  `idstudent` int NOT NULL,
  `joined_date` date DEFAULT NULL,
  `status` enum('active','completed','dropped') NOT NULL DEFAULT 'active',
  KEY `PRIMARY KEY` (`idproject_group`),
  KEY `fk_pg_project_idx` (`idproject`),
  KEY `fk_pg_student_idx` (`idstudent`),
  CONSTRAINT `fk_pg_project` FOREIGN KEY (`idproject`) REFERENCES `project` (`idproject`),
  CONSTRAINT `fk_pg_student` FOREIGN KEY (`idstudent`) REFERENCES `student` (`idstudent`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_group`
--

LOCK TABLES `project_group` WRITE;
/*!40000 ALTER TABLE `project_group` DISABLE KEYS */;
INSERT INTO `project_group` VALUES (1,1,2,'2025-01-15','active');
/*!40000 ALTER TABLE `project_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `project_requirement`
--

DROP TABLE IF EXISTS `project_requirement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_requirement` (
  `idproject` int NOT NULL,
  `idcourse` int NOT NULL,
  PRIMARY KEY (`idproject`,`idcourse`),
  KEY `fk_project_requirment_course_idx` (`idcourse`),
  CONSTRAINT `fk_project_requirment_course` FOREIGN KEY (`idcourse`) REFERENCES `course` (`idcourse`),
  CONSTRAINT `fk_project_requirment_project` FOREIGN KEY (`idproject`) REFERENCES `project` (`idproject`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `project_requirement`
--

LOCK TABLES `project_requirement` WRITE;
/*!40000 ALTER TABLE `project_requirement` DISABLE KEYS */;
INSERT INTO `project_requirement` VALUES (1,3),(2,3),(2,4),(1,6),(2,7),(1,8);
/*!40000 ALTER TABLE `project_requirement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student`
--

DROP TABLE IF EXISTS `student`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student` (
  `idstudent` int NOT NULL AUTO_INCREMENT,
  `student_number` varchar(20) NOT NULL,
  `fname` varchar(30) NOT NULL,
  `lname` varchar(30) NOT NULL,
  `email` varchar(60) NOT NULL,
  `study_right` varchar(60) NOT NULL,
  `valid_from` date NOT NULL,
  `valid_until` date NOT NULL,
  PRIMARY KEY (`idstudent`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student`
--

LOCK TABLES `student` WRITE;
/*!40000 ALTER TABLE `student` DISABLE KEYS */;
INSERT INTO `student` VALUES (1,'H123456','Aleksandr','Starchenkov','aleksandr.starchenkov@tuni.fi','Insinööri (AMK), tietotekniikka','2024-08-01','2028-07-31'),
(2,'H234567','Anna','Mäkinen','anna.makinen@tuni.fi','Insinööri (AMK), tietotekniikka','2024-08-01','2028-07-31'),
(3,'H345678','Mikko','Leinonen','mikko.leinonen@tuni.fi','Insinööri (AMK), tietotekniikka','2024-08-01','2028-07-31'),
(4,'H456789','Sofia','Nieminen','sofia.nieminen@tuni.fi','Insinööri (AMK), tietotekniikka','2024-08-01','2028-07-31'),
(5,'H567890','Eetu','Hakala','eetu.hakala@tuni.fi','Insinööri (AMK), tietotekniikka','2025-08-01','2029-07-31');
/*!40000 ALTER TABLE `student` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student_group`
--

DROP TABLE IF EXISTS `student_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student_group` (
  `idstudent` int NOT NULL,
  `idgroup` int NOT NULL,
  PRIMARY KEY (`idstudent`,`idgroup`),
  KEY `fk_srudent_group_group_cohort_idx` (`idgroup`),
  CONSTRAINT `fk_student_group_group_cohort` FOREIGN KEY (`idgroup`) REFERENCES `group_cohort` (`idgroup_cohort`),
  CONSTRAINT `fk_student_group_student` FOREIGN KEY (`idstudent`) REFERENCES `student` (`idstudent`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student_group`
--

LOCK TABLES `student_group` WRITE;
/*!40000 ALTER TABLE `student_group` DISABLE KEYS */;
INSERT INTO `student_group` VALUES (1,1),(2,1),(3,1),(4,1),(1,2),(5,2);
/*!40000 ALTER TABLE `student_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teacher`
--

DROP TABLE IF EXISTS `teacher`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teacher` (
  `idteacher` int NOT NULL AUTO_INCREMENT,
  `fname` varchar(30) NOT NULL,
  `lname` varchar(30) NOT NULL,
  `email` varchar(60) NOT NULL,
  PRIMARY KEY (`idteacher`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teacher`
--

LOCK TABLES `teacher` WRITE;
/*!40000 ALTER TABLE `teacher` DISABLE KEYS */;
INSERT INTO `teacher` VALUES (1,'Matti','Virtanen','matti.virtanen@tamk.fi'),(2,'Liisa','Korhonen','liisa.korhonen@tamk.fi');
/*!40000 ALTER TABLE `teacher` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `teacher_query_log`
--

DROP TABLE IF EXISTS `teacher_query_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `teacher_query_log` (
  `idlog` int NOT NULL AUTO_INCREMENT,
  `idteacher` int NOT NULL,
  `query_text` mediumtext NOT NULL,
  `intent` varchar(40) DEFAULT NULL,
  `result` mediumtext,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `PRIMARY KEY` (`idlog`),
  KEY `fk_log_teacher_idx` (`idteacher`),
  CONSTRAINT `fk_log_teacher` FOREIGN KEY (`idteacher`) REFERENCES `teacher` (`idteacher`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `teacher_query_log`
--

LOCK TABLES `teacher_query_log` WRITE;
/*!40000 ALTER TABLE `teacher_query_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `teacher_query_log` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-03 12:46:15
