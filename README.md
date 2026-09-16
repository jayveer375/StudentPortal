# Exam Seating Arrangement Email System

A simple Flask-based system to extract seating arrangements from PDF files and send personalized emails to students.

## Features

- Upload PDF seating arrangement files
- Extract student enrollment numbers and seating details
- Match students with PostgreSQL database
- Send personalized emails to each student
- Simple and clean web interface

## Setup Instructions

### 1. Prerequisites

- Python 3.7+
- PostgreSQL database
- Gmail account with App Password

### 2. Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE student_db;
```

2. Run the setup script:
```bash
psql -U your_username -d student_db -f database_setup.sql
```

### 3. Python Environment

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```env
# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=student_db
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password

# Email Configuration
EMAIL_ADDRESS=jayveervora47@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 4. Gmail App Password Setup

1. Go to Google Account settings
2. Enable 2-factor authentication
3. Generate App Password for "Mail"
4. Use this app password in the `.env` file

### 5. Run the Application

```bash
python app.py
```

Access the application at: http://localhost:5000

## Usage

1. **Upload PDF**: Select and upload the seating arrangement PDF file
2. **Review Results**: Check matched and not-found students
3. **Send Emails**: Click "Send Emails" to send personalized emails

## Project Structure

```
exam_seating_system/
│
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── database_setup.sql    # PostgreSQL setup script
├── sample_pdf_format.txt # Expected PDF format
├── README.md            # This file
│
├── templates/
│   └── index.html       # Main web page
│
├── static/
│   ├── style.css        # CSS styles
│   └── script.js        # JavaScript functionality
│
└── uploads/             # PDF upload directory
    └── .gitkeep
```

## Student Data

The system works with the existing `students` table containing:
- name
- enrollment_number (12-digit unique identifier)
- semester
- branch
- college_name
- email

## PDF Format

The PDF should contain:
- Student enrollment numbers (12-digit format)
- Semester information (SEM X)
- Block information
- Room numbers
- Subject code
- Date and time

See `sample_pdf_format.txt` for reference.

## Email Format

Each student receives a personalized email with:
```
Dear [Student Name],

Your exam seating arrangement is:

Name: [Student Name]
Enrollment No.: [Enrollment Number]
Block: [Block]
Semester: SEM [Semester]
Room Number: [Room]
Subject Code: [Subject Code]
Date: [Date]
Time: [Time]

Please report to the examination block on time.

Regards,
Government Polytechnic Ahmedabad
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL is running
   - Verify database credentials in `.env`
   - Ensure database and table exist

2. **Email Sending Failed**
   - Check Gmail App Password is correct
   - Verify SMTP settings
   - Ensure internet connection

3. **PDF Processing Error**
   - Check PDF file is not corrupted
   - Ensure PDF contains text (not scanned images)
   - Verify enrollment numbers are in 12-digit format

4. **No Students Matched**
   - Check enrollment numbers in PDF match database
   - Verify database contains student records
   - Check for typos in enrollment numbers

## Security Notes

- Never commit `.env` file with real credentials
- Use Gmail App Password, not regular password
- Ensure PostgreSQL has proper access controls
- Run on trusted networks only

## Limitations

- Basic PDF text extraction (may need adjustment for complex layouts)
- No authentication system (intended for admin use)
- Single-threaded email sending (suitable for small batches)
- Simple error handling (for educational purposes)