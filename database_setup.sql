-- Database Setup for Exam Seating Arrangement System
-- Run this script in PostgreSQL to set up the database and sample data

-- Create database (run this as postgres user)
-- CREATE DATABASE student_db;

-- Connect to student_db and run the following:

-- Create students table (if it doesn't exist)
-- Create students table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    enrollment_number BIGINT UNIQUE NOT NULL,
    semester INTEGER NOT NULL,
    branch VARCHAR(50) NOT NULL,
    college_name VARCHAR(200) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    password VARCHAR(255)
);

-- Create seating_arrangements table for uploaded batches
CREATE TABLE IF NOT EXISTS seating_arrangements (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    total_students INT DEFAULT 0,
    is_allocated BOOLEAN DEFAULT FALSE,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    allocated_at TIMESTAMP NULL
);

-- Create seating_allocations table for persistent classroom seat allotments (supports multiple classes per student)
CREATE TABLE IF NOT EXISTS seating_allocations (
    id SERIAL PRIMARY KEY,
    arrangement_id INT REFERENCES seating_arrangements(id) ON DELETE CASCADE,
    enrollment_number BIGINT NOT NULL,
    student_name VARCHAR(100),
    email VARCHAR(100),
    semester VARCHAR(20),
    branch VARCHAR(50),
    college_name VARCHAR(200),
    block VARCHAR(50),
    room VARCHAR(50),
    subject VARCHAR(100),
    date VARCHAR(50),
    time VARCHAR(50),
    is_allocated BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample student records
INSERT INTO students (name, enrollment_number, semester, branch, college_name, email, phone_number, password) VALUES 
('Jayveer vora', 246171063001, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'jayveervora47@gmail.com', '9876543210', NULL),
('Aarav Patwa', 246171063003, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'jayveervora48@gmail.com', '9876543211', NULL),
('Prakash Vora', 246171063005, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'voraprakash999@gmail.com', '9876543212', NULL),
('Sheetal vora', 246171063006, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'sheetalvora2006@gmail.com', '9876543213', NULL),
('Darshan tadha', 246171063009, 4, 'Computer', 'Government Polytechnic Ahmedabad', 'darshantadha504@gmail.com', '9876543214', NULL),
('Uber test', 216170307039, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'ubertestjayveer@gmail.com', '9876543215', NULL),
('Akshar shah', 216170307048, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'aksharclasses.ed@gmail.com', '9876543216', NULL),
('Bhavesh shimpi', 216170307228, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'chahatcare.2020@gmail.com', '9876543217', NULL),
('Het thakkar', 226178307016, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'schemalens4@gmail.com', '9876543218', NULL),
('Veer shah', 236170307002, 6, 'Computer', 'Government Polytechnic Ahmedabad', 'secrnb2023@gmail.com', '9876543219', NULL)
ON CONFLICT (enrollment_number) DO NOTHING;

-- Verify the data
SELECT * FROM students ORDER BY enrollment_number;
SELECT * FROM seating_allocations ORDER BY enrollment_number;