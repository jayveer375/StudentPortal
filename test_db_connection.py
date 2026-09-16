#!/usr/bin/env python3
"""
Test script to verify PostgreSQL database connection and student data.
Run this script to ensure your database is properly configured.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

def test_database_connection():
    """Test database connection and display student data."""
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Connect to database
        print("Connecting to PostgreSQL database...")
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Test query
        cursor.execute("SELECT COUNT(*) as student_count FROM students")
        count_result = cursor.fetchone()
        
        print(f"✅ Database connection successful!")
        print(f"✅ Found {count_result['student_count']} students in the database")
        
        # Display all students
        cursor.execute("SELECT * FROM students ORDER BY enrollment_number")
        students = cursor.fetchall()
        
        print("\n📋 Student Records:")
        print("-" * 80)
        for student in students:
            print(f"Name: {student['name']}")
            print(f"Enrollment: {student['enrollment_number']}")
            print(f"Semester: {student['semester']}")
            print(f"Branch: {student['branch']}")
            print(f"Email: {student['email']}")
            print("-" * 40)
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Check the following:")
        print("1. PostgreSQL is running")
        print("2. Database 'student_db' exists")
        print("3. Credentials in .env file are correct")
        print("4. Run database_setup.sql to create table and data")
        return False

def test_email_config():
    """Test email configuration."""
    
    load_dotenv()
    
    email_address = os.getenv('EMAIL_ADDRESS')
    email_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = os.getenv('SMTP_PORT')
    
    print("\n📧 Email Configuration:")
    print("-" * 40)
    print(f"Email Address: {email_address}")
    print(f"Password Set: {'✅ Yes' if email_password else '❌ No'}")
    print(f"SMTP Server: {smtp_server}")
    print(f"SMTP Port: {smtp_port}")
    
    if not all([email_address, email_password, smtp_server, smtp_port]):
        print("\n❌ Email configuration incomplete!")
        print("🔧 Please set all email variables in .env file")
        return False
    else:
        print("\n✅ Email configuration looks good!")
        print("📝 Note: Make sure to use Gmail App Password, not regular password")
        return True

if __name__ == "__main__":
    print("🔍 Testing Exam Seating System Configuration")
    print("=" * 50)
    
    # Test database
    db_ok = test_database_connection()
    
    # Test email config
    email_ok = test_email_config()
    
    print("\n" + "=" * 50)
    if db_ok and email_ok:
        print("✅ All tests passed! Your system is ready to run.")
        print("🚀 Start the application with: python app.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    
    print("=" * 50)