-- Database Setup for Exam Seating Arrangement System
-- Run this script in PostgreSQL to set up the database and sample data

-- Create database (run this as postgres user)
-- CREATE DATABASE student_db;

-- Connect to student_db and run the following:

-- Create students table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    enrollment_number BIGINT UNIQUE NOT NULL,
    semester INTEGER NOT NULL,
    branch VARCHAR(50) NOT NULL,
    college_name VARCHAR(200) NOT NULL,
    email VARCHAR(100) NOT NULL
);

-- Insert sample student records
INSERT INTO students (name, enrollment_number, semester, branch, college_name, email) VALUES 
('Jayveer vora', 246171063001, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'jayveervora47@gmail.com'),
('Aarav Patwa', 246171063003, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'jayveervora48@gmail.com'),
('Prakash Vora', 246171063005, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'voraprakash999@gmail.com'),
('Sheetal vora', 246171063006, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'sheetalvora2006@gmail.com'),
('Darshan tadha', 246171063009, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'darshantadha504@gmail.com'),
('Uber test', 216170307039, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'ubertestjayveer@gmail.com'),
('Akshar shah', 216170307048, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'aksharclasses.ed@gmail.com'),
('Bhavesh shimpi', 216170307228, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'chahatcare.2020@gmail.com'),
('Het thakkar', 226178307016, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'schemalens4@gmail.com'),
('Veer shah', 236170307002, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'secrnb2023@gmail.com')
ON CONFLICT (enrollment_number) DO NOTHING;

-- Verify the data
SELECT * FROM students ORDER BY enrollment_number;