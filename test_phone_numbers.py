#!/usr/bin/env python3
"""
Test script to check phone numbers in the database
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

def test_phone_numbers():
    load_dotenv()
    
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'), 
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if phone column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'students' AND column_name = 'phone_number';
        """)
        phone_column = cursor.fetchone()
        
        if phone_column:
            print('✅ Phone column exists')
            
            # Get all students with their phone numbers
            cursor.execute('SELECT name, enrollment_number, email, phone_number FROM students ORDER BY enrollment_number')
            students = cursor.fetchall()
            
            print('\n📋 All students and their phone numbers:')
            for student in students:
                phone = student.get('phone_number') or 'NULL'
                print(f'{student["name"]} ({student["enrollment_number"]}): {phone}')
                
            # Get only students with phone numbers
            cursor.execute('SELECT name, enrollment_number, phone_number FROM students WHERE phone_number IS NOT NULL AND phone_number != \'\'')
            students_with_phone = cursor.fetchall()
            
            print(f'\n📱 Students with phone numbers: {len(students_with_phone)}')
            for student in students_with_phone:
                print(f'{student["name"]}: {student["phone_number"]}')
                
        else:
            print('❌ Phone column does not exist')
            
            # Show current table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'students' 
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            print('\nCurrent table structure:')
            for col in columns:
                print(f'{col["column_name"]}: {col["data_type"]}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'Database error: {e}')

if __name__ == "__main__":
    test_phone_numbers()