import os
import re
import smtplib
import time
import threading
from functools import wraps
from datetime import timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor
import PyPDF2
import openpyxl
from dotenv import load_dotenv
import json
import uuid
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = os.getenv('SECRET_KEY', 'examdesk-gtu-secure-session-key-2026')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
app.config['TEMPLATES_AUTO_RELOAD'] = True   # Always reload templates

# Single Administrator Credentials
ADMIN_EMAIL = "Admin@gmail.com"
ADMIN_PASSWORD = "admin@123"

# Authentication enforcement decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if (
                request.is_json
                or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or request.path.startswith('/upload')
                or request.path.startswith('/send_')
                or request.path.startswith('/email_')
                or request.path.startswith('/whatsapp_')
                or request.path.startswith('/cancel_')
                or request.path.startswith('/close_')
            ):
                return jsonify({
                    'error': 'Authentication required. Please login as Administrator.',
                    'redirect': url_for('login')
                }), 401
            return redirect(url_for('login', next=request.url))
            
        role = session.get('role')
        if role == 'student':
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'error': 'Access denied. Administrator privileges required.',
                    'redirect': url_for('student_portal')
                }), 403
            return redirect(url_for('student_portal'))
        elif role != 'admin':
            session.clear()
            return redirect(url_for('login'))
            
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'error': 'Authentication required. Please login first.',
                    'redirect': url_for('login')
                }), 401
            return redirect(url_for('login', next=request.url))
            
        role = session.get('role')
        if role == 'admin':
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'error': 'Access denied. Student portal only.',
                    'redirect': url_for('index')
                }), 403
            return redirect(url_for('index'))
        elif role != 'student':
            session.clear()
            return redirect(url_for('login'))
            
        return f(*args, **kwargs)
    return decorated_function

# Maintain login_required as alias to admin_required for all existing admin routes
login_required = admin_required

# Disable browser caching for all responses
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables for email progress tracking
email_progress = {}
email_sessions = {}

# Global variables for WhatsApp progress tracking
whatsapp_progress = {}
whatsapp_sessions = {}
whatsapp_driver = None

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    return conn

# Extract text from PDF
def extract_pdf_text(pdf_path):
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

# Parse seating arrangement from PDF text
def parse_seating_info(pdf_text):
    seating_data = []
    
    print("PDF Text for debugging:")
    print("=" * 50)
    print(pdf_text)
    print("=" * 50)
    
    # Extract enrollment numbers (12-digit numbers)
    enrollment_pattern = r'\b\d{12}\b'
    enrollments = re.findall(enrollment_pattern, pdf_text)
    print(f"Found enrollments: {enrollments}")
    
    # Extract date - looking for patterns like "12 sept 2026"
    date_patterns = [
        r'(\d{1,2}\s+sept\s+\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}-\d{1,2}-\d{4})',
        r'DATE[:\s]*(\d{1,2}\s+\w+\s+\d{4})'
    ]
    date_matches = []
    for pattern in date_patterns:
        matches = re.findall(pattern, pdf_text, re.IGNORECASE)
        if matches:
            date_matches.extend(matches)
    
    # Extract time - looking for "10:30 AM TO 1:00 PM"
    time_patterns = [
        r'(\d{1,2}:\d{2}\s*AM\s+TO\s+\d{1,2}:\d{2}\s*PM)',
        r'(\d{1,2}:\d{2}\s*(?:AM|PM)[^\n]*\d{1,2}:\d{2}\s*(?:AM|PM))',
        r'TIME[:\s]*(\d{1,2}:\d{2}[^\n]*\d{1,2}:\d{2}[^\n]*)'
    ]
    time_matches = []
    for pattern in time_patterns:
        matches = re.findall(pattern, pdf_text, re.IGNORECASE)
        if matches:
            time_matches.extend(matches)
    
    # Extract subject codes - 4 to 10 digit codes (e.g. 41046307, 4360709)
    subject_pattern = r'\b\d{4,10}\b'
    subject_matches = re.findall(subject_pattern, pdf_text)
    # Filter out numbers that are clearly not subject codes:
    # enrollment numbers (12 digits) are already excluded by the \b\d{4,10}\b range.
    # Also exclude pure year numbers like 2026 and block/total numbers (1-3 digits).
    subject_matches = [s for s in subject_matches if 4 <= len(s) <= 10 and s not in ('2026', '2025', '2024')]
    
    # Extract room numbers - looking for patterns like "1A110", "1A112 P"
    room_patterns = [
        r'\b(\d[A-Z]\d+(?:\s+[A-Z])?)\b',  # Matches 1A110, 1A112 P
        r'ROOM\s*NO[:\s]*([A-Z0-9\s]+)',
        r'(\d+[A-Z]\d+[A-Z]*)'
    ]
    room_matches = []
    for pattern in room_patterns:
        matches = re.findall(pattern, pdf_text, re.IGNORECASE)
        if matches:
            room_matches.extend(matches)
    
    # Extract block numbers - from the table structure
    block_patterns = [
        r'BLOCK\s+NO[:\s]*(\d+)',
        r'(\d+)\s*\(SEM\d+\)',  # Matches "1 (SEM4)"
        r'BLOCK[:\s]*(\d+)'
    ]
    block_matches = []
    for pattern in block_patterns:
        matches = re.findall(pattern, pdf_text, re.IGNORECASE)
        if matches:
            block_matches.extend(matches)
    
    # Extract semester info
    semester_patterns = [
        r'FOURTH\s+&\s+SIXTH\s+SEMESTER',
        r'SEM\s*(\d+)',
        r'(\d+)\s*\(SEM(\d+)\)'
    ]
    semester_matches = []
    for pattern in semester_patterns:
        matches = re.findall(pattern, pdf_text, re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                semester_matches.extend([m for m in matches[0] if m.isdigit()])
            else:
                semester_matches.extend(matches)
    
    print(f"Date matches: {date_matches}")
    print(f"Time matches: {time_matches}")
    print(f"Subject matches: {subject_matches}")
    print(f"Room matches: {room_matches}")
    print(f"Block matches: {block_matches}")
    print(f"Semester matches: {semester_matches}")
    
    # Map each enrollment to its group by finding which SEM-block it belongs to.
    # Parse rows like "1 (SEM4)  1A110  41046307  enr1  enr2 ..." from the PDF text.
    # Each data line starts with subject code, followed by enrollments, then block info.
    seating_data = []
    # Split text into lines and look for lines containing (SEM\d+)
    # Fall back to positional split only if SEM markers are absent.
    sem_row_pattern = re.compile(
        r'(\d{4,10})\s+'           # subject code
        r'((?:\d{12}\s*)+)'        # one or more enrollment numbers
        r'.*?(\d+)\s*\(SEM(\d+)\)' # block (SEMX)
        r'\s*([\dA-Z]+(?:\s+[A-Z])?)',  # room
        re.IGNORECASE | re.DOTALL
    )

    structured_rows = sem_row_pattern.findall(pdf_text)
    print(f"Structured rows from PDF: {structured_rows}")

    if structured_rows:
        # Use the structured extraction — accurate regardless of student count
        for row in structured_rows:
            subject_code = row[0]
            row_enrollments = re.findall(r'\d{12}', row[1])
            block = row[2]
            semester = row[3]
            room = row[4].strip()
            for enrollment in row_enrollments:
                seating_data.append({
                    'enrollment_number': enrollment,
                    'block':    block,
                    'room':     room,
                    'subject':  subject_code,
                    'date':     date_matches[0] if date_matches else 'N/A',
                    'time':     time_matches[0] if time_matches else 'N/A',
                    'semester': semester,
                })
    else:
        # Fallback: positional split (original behaviour)
        print("Warning: could not parse structured rows — using positional fallback")
        sem4_enrollments = enrollments[:5] if len(enrollments) >= 5 else enrollments
        sem6_enrollments = enrollments[5:] if len(enrollments) > 5 else []

        for enrollment in sem4_enrollments:
            seating_data.append({
                'enrollment_number': enrollment,
                'block':    block_matches[0] if block_matches else '1',
                'room':     room_matches[0] if room_matches else '1A110',
                'subject':  subject_matches[0] if subject_matches else 'N/A',
                'date':     date_matches[0] if date_matches else 'N/A',
                'time':     time_matches[0] if time_matches else 'N/A',
                'semester': '4',
            })
        for enrollment in sem6_enrollments:
            seating_data.append({
                'enrollment_number': enrollment,
                'block':    block_matches[1] if len(block_matches) > 1 else '2',
                'room':     room_matches[1] if len(room_matches) > 1 else '1A112 P',
                'subject':  subject_matches[1] if len(subject_matches) > 1 else 'N/A',
                'date':     date_matches[0] if date_matches else 'N/A',
                'time':     time_matches[0] if time_matches else 'N/A',
                'semester': '6',
            })

    return seating_data

# Parse seating arrangement from Excel file
def parse_excel_seating_info(excel_path):
    """
    Parses GTU seating arrangement Excel files in any format.

    Approach — header-keyword driven, not positional or regex-pattern driven:

    1. Un-merge: fill every cell in a merged region with the top-left value so
       continuation rows carry the same subject/room/block as the first row.

    2. Scan ALL cells to collect full-sheet text for date/time extraction.

    3. Find the header row by searching every row for known GTU column keywords
       (SUBJECT, ROOM, BLOCK, SEMESTER, STUDENT SEAT NO., etc.).
       Once found, record which column index holds which field.

    4. Walk every data row below the header row:
       - Read subject, room, block, semester directly from their detected columns.
       - Collect every 12-digit enrollment number from the enrollment columns.
       - If a field column is empty in a row (merged cell continuation), keep
         the last seen non-empty value for that field.

    This means the parser works regardless of:
    - How many enrollment columns there are
    - What the room number looks like (08104 P AUTO, 1A110, Lab-3, anything)
    - Whether the format changes column order in future
    """
    seating_data = []

    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        ws = wb.active

        # ------------------------------------------------------------------
        # Step 1: Un-merge — fill every cell of a merged region with the
        #         top-left cell's value so continuation rows are not empty
        # ------------------------------------------------------------------
        merged_values = {}
        for merge_range in ws.merged_cells.ranges:
            top_left_val = ws.cell(merge_range.min_row, merge_range.min_col).value
            for r in range(merge_range.min_row, merge_range.max_row + 1):
                for c in range(merge_range.min_col, merge_range.max_col + 1):
                    merged_values[(r, c)] = top_left_val

        # Build a 2-D grid: grid[row_idx] = [cell_value_as_string, ...]
        # Empty/None cells become '' so column indices stay aligned.
        grid = []
        all_text_parts = []
        for row in ws.iter_rows():
            row_cells = []
            for cell in row:
                val = merged_values.get((cell.row, cell.column), cell.value)
                s = str(val).strip() if val is not None else ''
                row_cells.append(s)
                if s:
                    all_text_parts.append(s)
            grid.append(row_cells)

        full_text = ' '.join(all_text_parts)
        print("=== Excel full text (first 600 chars) ===")
        print(full_text[:600])

        # ------------------------------------------------------------------
        # Step 2: Extract date and time from full sheet text
        # ------------------------------------------------------------------
        date_val = 'N/A'
        for pat in [
            r'(\d{1,2}\s+\w+\s+\d{4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
        ]:
            m = re.search(pat, full_text, re.IGNORECASE)
            if m:
                date_val = m.group(1).strip()
                break

        time_val = 'N/A'
        for pat in [
            r'(\d{1,2}[.:]\d{2}\s*AM\s+TO\s+\d{1,2}[.:]\d{2}\s*PM)',
            r'(\d{1,2}[.:]\d{2}\s*(?:AM|PM).*?\d{1,2}[.:]\d{2}\s*(?:AM|PM))',
        ]:
            m = re.search(pat, full_text, re.IGNORECASE)
            if m:
                time_val = m.group(1).strip()
                break

        print(f"Date: {date_val} | Time: {time_val}")

        # ------------------------------------------------------------------
        # Step 3: Find the header row by keyword matching
        #
        # GTU Excel header keywords we look for (case-insensitive):
        #   SUBJECT / SUB CODE / SUBJECT CODE  → subject column
        #   ROOM / ROOM NO / HALL              → room column
        #   BLOCK                              → block column
        #   SEM / SEMESTER                     → semester column
        #   STUDENT SEAT NO / ENROLLMENT / ENR → enrollment columns (can be many)
        #
        # We scan every row until we find one that contains at least
        # SUBJECT and one enrollment/seat keyword.
        # ------------------------------------------------------------------
        SUBJECT_KEYWORDS    = ['subject', 'sub code', 'subject code']
        ROOM_KEYWORDS       = ['room', 'room no', 'hall', 'examination hall']
        BLOCK_KEYWORDS      = ['block']
        SEM_KEYWORDS        = ['sem', 'semester']
        ENROLL_KEYWORDS     = ['student seat', 'enrollment', 'enroll', 'seat no', 'roll']

        header_row_idx  = None
        subject_col     = None
        room_col        = None
        block_col       = None
        sem_col         = None
        enroll_cols     = []   # may span multiple columns

        for row_idx, row_cells in enumerate(grid):
            row_lower = [c.lower() for c in row_cells]

            # Check if this row has a SUBJECT keyword cell
            sub_found = None
            for ci, cell in enumerate(row_lower):
                if any(kw in cell for kw in SUBJECT_KEYWORDS):
                    sub_found = ci
                    break

            if sub_found is None:
                continue  # not a header row, keep scanning

            # Found a subject keyword — now map all other columns
            subject_col = sub_found
            for ci, cell in enumerate(row_lower):
                if any(kw in cell for kw in ROOM_KEYWORDS):
                    room_col = ci
                elif any(kw in cell for kw in BLOCK_KEYWORDS):
                    block_col = ci
                elif any(kw in cell for kw in SEM_KEYWORDS) and ci != subject_col:
                    sem_col = ci
                elif any(kw in cell for kw in ENROLL_KEYWORDS):
                    enroll_cols.append(ci)

            if enroll_cols:
                header_row_idx = row_idx
                print(f"Header found at row {row_idx}: subject_col={subject_col}, "
                      f"room_col={room_col}, block_col={block_col}, "
                      f"sem_col={sem_col}, enroll_cols={enroll_cols}")
                break

        # ------------------------------------------------------------------
        # Step 4: Walk data rows below the header
        #
        # For each row:
        #   - Read subject, room, block, sem from their named columns.
        #   - If a cell is empty (merged continuation), reuse the last value.
        #   - Collect 12-digit enrollment numbers from all enrollment columns
        #     AND from any other cell in the row that looks like an enrollment.
        # ------------------------------------------------------------------
        enrollment_re = re.compile(r'^\d{12}$')

        if header_row_idx is None:
            # No header found — fall back: treat every 12-digit number in the
            # sheet as an enrollment and leave metadata as N/A
            print("WARNING: No header row found. Extracting all 12-digit numbers.")
            for row_cells in grid:
                for cell in row_cells:
                    if enrollment_re.match(cell):
                        seating_data.append({
                            'enrollment_number': cell,
                            'subject': 'N/A', 'block': 'N/A',
                            'room': 'N/A', 'date': date_val,
                            'time': time_val, 'semester': 'N/A',
                        })
        else:
            last_subject = 'N/A'
            last_room    = 'N/A'
            last_block   = 'N/A'
            last_sem     = 'N/A'

            for row_cells in grid[header_row_idx + 1:]:
                # Read named-column values; keep last non-empty for merged rows
                def col_val(col_idx):
                    if col_idx is None:
                        return ''
                    v = row_cells[col_idx] if col_idx < len(row_cells) else ''
                    return v.strip()

                subject_cell = col_val(subject_col)
                room_cell    = col_val(room_col)
                block_cell   = col_val(block_col)
                sem_cell     = col_val(sem_col)

                # Update last-seen values when cells are non-empty
                if subject_cell:
                    last_subject = subject_cell
                if room_cell:
                    last_room = room_cell
                if block_cell:
                    last_block = block_cell
                if sem_cell:
                    last_sem = sem_cell

                # Collect enrollments from named enroll columns first
                enrollments = []
                for ec in enroll_cols:
                    v = col_val(ec)
                    if enrollment_re.match(v):
                        enrollments.append(v)

                # Also sweep entire row for any 12-digit number not yet captured
                # This handles sheets where enrollment columns span further than
                # the header labels cover
                for cell in row_cells:
                    if enrollment_re.match(cell) and cell not in enrollments:
                        enrollments.append(cell)

                if not enrollments:
                    continue

                # Extract semester number from block/sem text if sem_col missing
                sem_final = last_sem
                if sem_final == 'N/A' or not re.search(r'\d', sem_final):
                    sm = re.search(r'SEM\s*(\d+)', last_block, re.IGNORECASE)
                    if sm:
                        sem_final = sm.group(1)

                # Extract block number from block text
                block_final = last_block
                bm = re.match(r'^(\d+)', last_block)
                if bm:
                    block_final = bm.group(1)

                print(f"Subject={last_subject} | Room={last_room} | "
                      f"Block={block_final} | SEM={sem_final} | "
                      f"Enrollments={enrollments}")

                for enr in enrollments:
                    seating_data.append({
                        'enrollment_number': enr,
                        'subject':  last_subject,
                        'block':    block_final,
                        'room':     last_room,
                        'date':     date_val,
                        'time':     time_val,
                        'semester': sem_final,
                    })

        print(f"Parsed {len(seating_data)} records from Excel")

    except Exception as e:
        import traceback
        print(f"Error reading Excel file: {e}")
        traceback.print_exc()

    return seating_data

# Match students with database
def match_students_with_db(seating_data):
    matched_students = []
    not_found_students = []
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        for seating in seating_data:
            enrollment = seating['enrollment_number']
            cursor.execute(
                "SELECT * FROM students WHERE enrollment_number = %s",
                (enrollment,)
            )
            student = cursor.fetchone()
            
            if student:
                matched_student = {
                    'name': student['name'],
                    'enrollment_number': student['enrollment_number'],
                    'email': student['email'],
                    'phone': student.get('phone_number', ''),
                    'semester': student['semester'],
                    'branch': student['branch'],
                    'college_name': student['college_name'],
                    'block': seating['block'],
                    'room': seating['room'],
                    'subject': seating['subject'],
                    'date': seating['date'],
                    'time': seating['time']
                }
                matched_students.append(matched_student)
            else:
                not_found_students.append(enrollment)
        
        cursor.close()

    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    return matched_students, not_found_students

# Validate an email address — checks format and that the domain has an MX record.
# Returns (True, '') if valid, (False, reason_string) if not.
def validate_email_address(email):
    # 1. Empty or None
    if not email or not str(email).strip():
        return False, 'Email is empty or missing'

    email = str(email).strip()

    # 2. Basic format check — must have exactly one @, non-empty local and domain parts
    email_format_re = re.compile(
        r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    )
    if not email_format_re.match(email):
        return False, f'Invalid email format: {email}'

    # 3. Domain MX record check — confirms the domain can actually receive mail
    domain = email.split('@')[1]
    try:
        import socket
        # Query MX record via DNS. socket.getaddrinfo on the domain is a lightweight
        # connectivity check; a proper MX lookup requires dnspython but we avoid
        # extra dependencies by checking if the domain resolves at all.
        socket.setdefaulttimeout(5)
        socket.gethostbyname(domain)
    except socket.gaierror:
        return False, f'Domain does not exist or cannot receive mail: {domain}'
    except Exception:
        # If DNS check fails for any other reason, allow the email through —
        # we don't want network hiccups to block valid emails.
        pass

    return True, ''


# Send email to student with progress tracking
def send_email_with_progress(student_data, session_id, index, total):
    try:
        # Update progress - sending
        email_progress[session_id]['current'] = index + 1
        email_progress[session_id]['status'] = f"Sending email to {student_data['name']}..."
        
        # Email configuration
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT'))
        email_address = os.getenv('EMAIL_ADDRESS')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_address
        msg['To'] = student_data['email']
        msg['Subject'] = "Exam Seating Arrangement"
        
        # Email body
        body = f"""Dear {student_data['name']},

Your exam seating arrangement is:

Name: {student_data['name']}
Enrollment No.: {student_data['enrollment_number']}
Semester: SEM {student_data['semester']}
Branch: {student_data['branch']}

EXAM DETAILS:
Subject Code: {student_data['subject']}
Date: {student_data['date']}
Time: {student_data['time']}

LOCATION:
Block Number: {student_data['block']}
Room Number: {student_data['room']}

Please report to Block {student_data['block']}, Room {student_data['room']} on time.

Regards,
{student_data['college_name']}"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_address, email_password)
        server.send_message(msg)
        server.quit()
        
        # Update progress - sent successfully
        email_progress[session_id]['sent'] += 1
        email_progress[session_id]['status'] = f"✅ Email sent to {student_data['name']}"
        
        # Small delay to show progress (remove in production)
        time.sleep(0.5)
        
        return True
        
    except Exception as e:
        print(f"Email sending error: {e}")
        # Update progress - failed
        email_progress[session_id]['failed'] += 1
        email_progress[session_id]['failed_emails'].append({
            'name': student_data['name'],
            'enrollment': student_data['enrollment_number'],
            'error': str(e)
        })
        email_progress[session_id]['status'] = f"❌ Failed to send email to {student_data['name']}"
        return False

# WhatsApp automation using PyWhatKit (Alternative to Selenium)
def send_whatsapp_pywhatkit(phone_number, message, session_id, index, total):
    try:
        import pywhatkit as pwk
        import datetime
        
        # Update progress - sending
        whatsapp_progress[session_id]['current'] = index + 1
        whatsapp_progress[session_id]['status'] = f"Sending WhatsApp to {phone_number}..."
        
        # Format phone number for India
        clean_number = re.sub(r'[^\d]', '', phone_number)
        if clean_number.startswith('91') and len(clean_number) == 12:
            clean_number = clean_number[2:]
        
        # Add country code
        full_number = f"+91{clean_number}"
        
        print(f"Sending WhatsApp to {full_number}")
        
        # Get current time and add 1 minute for sending
        now = datetime.datetime.now()
        send_time = now + datetime.timedelta(minutes=1)
        
        # Send message using PyWhatKit
        pwk.sendwhatmsg(
            phone_no=full_number,
            message=message,
            time_hour=send_time.hour,
            time_min=send_time.minute,
            wait_time=10,  # Wait 10 seconds after opening
            tab_close=False  # Keep tab open for next message
        )
        
        print(f"✅ WhatsApp message scheduled for {full_number}")
        
        # Update progress - sent successfully
        whatsapp_progress[session_id]['sent'] += 1
        whatsapp_progress[session_id]['status'] = f"✅ WhatsApp sent to {phone_number}"
        
        return True
        
    except Exception as e:
        print(f"PyWhatKit error for {phone_number}: {e}")
        # Update progress - failed
        whatsapp_progress[session_id]['failed'] += 1
        whatsapp_progress[session_id]['failed_messages'].append({
            'phone': phone_number,
            'error': str(e)
        })
        whatsapp_progress[session_id]['status'] = f"❌ Failed to send WhatsApp to {phone_number}"
        return False

def send_whatsapp_messages_background_pywhatkit(students, session_id):
    total = len(students)
    
    # Initialize progress
    whatsapp_progress[session_id] = {
        'total': total,
        'current': 0,
        'sent': 0,
        'failed': 0,
        'status': 'Starting WhatsApp with PyWhatKit...',
        'completed': False,
        'failed_messages': []
    }
    
    print(f"Starting PyWhatKit WhatsApp batch {session_id} with {total} students")
    
    try:
        # Send messages one by one
        for i, student in enumerate(students):
            if session_id not in whatsapp_progress:  # Check if process was cancelled
                print(f"WhatsApp batch {session_id} was cancelled")
                return
                
            # Create WhatsApp message
            message = f"""🎓 *Exam Seating Arrangement*

Dear {student['name']},

Your exam details:
📝 *Subject:* {student['subject']}
📅 *Date:* {student['date']}
⏰ *Time:* {student['time']}

📍 *Location:*
🏢 Block: {student['block']}
🚪 Room: {student['room']}

Please report on time.

- {student['college_name']}"""
            
            print(f"Sending PyWhatKit message {i+1}/{total} to {student['name']}")
            send_whatsapp_pywhatkit(student.get('phone', ''), message, session_id, i, total)
            
            # Delay between messages (PyWhatKit handles most of the timing)
            if i < total - 1:  # Don't delay after the last message
                time.sleep(30)  # 30 seconds between messages for PyWhatKit
        
        # Mark as completed
        whatsapp_progress[session_id]['completed'] = True
        whatsapp_progress[session_id]['status'] = f"✅ PyWhatKit WhatsApp sending completed! Sent: {whatsapp_progress[session_id]['sent']}, Failed: {whatsapp_progress[session_id]['failed']}"
        print(f"PyWhatKit batch {session_id} completed. Sent: {whatsapp_progress[session_id]['sent']}, Failed: {whatsapp_progress[session_id]['failed']}")
        
    except Exception as e:
        print(f"PyWhatKit batch error: {e}")
        whatsapp_progress[session_id]['status'] = f"❌ PyWhatKit batch error: {str(e)}"
        whatsapp_progress[session_id]['completed'] = True

# Send emails in background thread
def send_emails_background(students, session_id):
    total = len(students)
    
    # Initialize progress
    email_progress[session_id] = {
        'total': total,
        'current': 0,
        'sent': 0,
        'failed': 0,
        'status': 'Starting email sending...',
        'completed': False,
        'failed_emails': []
    }
    
    print(f"Starting email batch {session_id} with {total} students")
    
    # Send emails one by one
    for i, student in enumerate(students):
        if session_id not in email_progress:  # Check if process was cancelled
            print(f"Email batch {session_id} was cancelled")
            return
            
        print(f"Sending email {i+1}/{total} to {student['name']}")
        send_email_with_progress(student, session_id, i, total)
    
    # Mark as completed
    email_progress[session_id]['completed'] = True
    email_progress[session_id]['status'] = f"✅ Email sending completed! Sent: {email_progress[session_id]['sent']}, Failed: {email_progress[session_id]['failed']}"
    print(f"Email batch {session_id} completed. Sent: {email_progress[session_id]['sent']}, Failed: {email_progress[session_id]['failed']}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('logged_in'):
            if session.get('role') == 'student':
                return redirect(url_for('student_portal'))
            return redirect(url_for('index'))
        return render_template('login.html')

    # POST request - support both JSON payload and standard form data
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or request.form.get('username') or '').strip()
    password = (data.get('password') or request.form.get('password') or '').strip()

    # 1. Check Administrator Credentials
    if username.lower() == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        session['role'] = 'admin'
        session['user_email'] = ADMIN_EMAIL
        session.permanent = True

        next_url = request.args.get('next') or url_for('index')
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'redirect': next_url})
        return redirect(next_url)

    # 2. Check Student Credentials from PostgreSQL
    student = None
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM students WHERE LOWER(email) = LOWER(%s)", (username,))
        student = cursor.fetchone()
        cursor.close()
    except Exception as e:
        print(f"Database authentication error: {e}")
    finally:
        if conn:
            conn.close()

    if student:
        # Determine valid password:
        # If student has updated password in database, match against it.
        # Otherwise, initial default password is the student's enrollment number.
        db_pwd = student.get('password')
        expected_pwd = db_pwd if (db_pwd and str(db_pwd).strip()) else str(student['enrollment_number']).strip()

        if password == expected_pwd:
            session['logged_in'] = True
            session['role'] = 'student'
            session['student_id'] = student['id']
            session['student_email'] = student['email']
            session['student_name'] = student['name']
            session['enrollment_number'] = student['enrollment_number']
            session.permanent = True

            next_url = request.args.get('next') or url_for('student_portal')
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'redirect': next_url})
            return redirect(next_url)

    error_msg = 'Invalid credentials. Please verify your Email and Password.'
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': error_msg}), 401
    flash(error_msg, 'error')
    return render_template('login.html', error=error_msg, username=username)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    # If not logged in, redirect to login page
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # If logged in as student, redirect to student portal
    if session.get('role') == 'student':
        return redirect(url_for('student_portal'))
    
    # Admin user - show main dashboard
    return render_template('index.html', admin_user=session.get('user_email', ADMIN_EMAIL))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename_lower = file.filename.lower()
    is_pdf   = filename_lower.endswith('.pdf')
    is_excel = filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls')

    if file and (is_pdf or is_excel):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        if is_pdf:
            pdf_text    = extract_pdf_text(filepath)
            seating_data = parse_seating_info(pdf_text)
        else:
            seating_data = parse_excel_seating_info(filepath)

        matched_students, not_found_students = match_students_with_db(seating_data)

        # Store in server-side session keyed by a unique upload token
        upload_token = str(uuid.uuid4())
        app.config.setdefault('upload_store', {})[upload_token] = matched_students

        # Persist arrangement batch and allocations into PostgreSQL with is_allocated = FALSE
        # The arrangement will only be visible to students after admin explicitly clicks "Allocate"
        arrangement_id = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Create seating_arrangements batch record
            cur.execute('''
                INSERT INTO seating_arrangements (filename, title, total_students, is_allocated, uploaded_at)
                VALUES (%s, %s, %s, FALSE, NOW())
                RETURNING id;
            ''', (file.filename, file.filename, len(matched_students)))
            arrangement_id = cur.fetchone()[0]

            for s in matched_students:
                cur.execute('''
                    INSERT INTO seating_allocations (
                        arrangement_id, enrollment_number, student_name, email, semester, 
                        branch, college_name, block, room, subject, date, time, is_allocated, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, NOW());
                ''', (
                    arrangement_id,
                    s['enrollment_number'],
                    s['name'],
                    s['email'],
                    str(s['semester']),
                    s['branch'],
                    s['college_name'],
                    s['block'],
                    s['room'],
                    s['subject'],
                    s['date'],
                    s['time']
                ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as persist_err:
            print(f"Error persisting seating arrangement to database: {persist_err}")

        return jsonify({
            'success': True,
            'upload_token': upload_token,
            'arrangement_id': arrangement_id,
            'filename': file.filename,
            'is_allocated': False,
            'matched_students': matched_students,
            'not_found_students': not_found_students,
            'total_extracted': len(seating_data),
            'total_matched': len(matched_students),
            'total_not_found': len(not_found_students)
        })

    return jsonify({'error': 'Invalid file type. Please upload a PDF or Excel (.xlsx / .xls) file.'}), 400

@app.route('/send_emails', methods=['POST'])
@login_required
def send_emails():
    data = request.get_json(silent=True) or {}
    upload_token = data.get('upload_token')
    upload_store = app.config.get('upload_store', {})
    matched_students = upload_store.get(upload_token, []) if upload_token else []

    if not matched_students:
        return jsonify({'error': 'No matched students found. Please upload and process a file first.'}), 400

    # --- Validate emails before sending ---
    valid_students   = []
    invalid_students = []   # list of {name, enrollment_number, email, reason}

    for student in matched_students:
        ok, reason = validate_email_address(student.get('email', ''))
        if ok:
            valid_students.append(student)
        else:
            invalid_students.append({
                'name':              student.get('name', 'Unknown'),
                'enrollment_number': student.get('enrollment_number', ''),
                'email':             student.get('email', ''),
                'reason':            reason,
            })

    # If every student has an invalid email, return early with the list
    if not valid_students:
        return jsonify({
            'success':         False,
            'error':           'No students with valid email addresses found.',
            'invalid_students': invalid_students,
        }), 400

    # Generate unique session ID for this email batch
    session_id = str(uuid.uuid4())
    email_sessions[session_id] = valid_students

    # Start background email sending — only for valid addresses
    thread = threading.Thread(target=send_emails_background, args=(valid_students, session_id))
    thread.daemon = True
    thread.start()

    return jsonify({
        'success':          True,
        'session_id':       session_id,
        'total_students':   len(valid_students),
        'invalid_students': invalid_students,
    })

@app.route('/email_progress/<session_id>')
@login_required
def get_email_progress(session_id):
    if session_id in email_progress:
        return jsonify(email_progress[session_id])
    else:
        return jsonify({'error': 'Session not found'}), 404

@app.route('/cancel_emails/<session_id>', methods=['POST'])
@login_required
def cancel_emails(session_id):
    if session_id in email_progress:
        del email_progress[session_id]
    if session_id in email_sessions:
        del email_sessions[session_id]
    return jsonify({'success': True, 'message': 'Email sending cancelled'})

# WhatsApp routes
@app.route('/send_whatsapp', methods=['POST'])
@login_required
def send_whatsapp():
    data = request.get_json(silent=True) or {}
    upload_token = data.get('upload_token')
    upload_store = app.config.get('upload_store', {})
    matched_students = upload_store.get(upload_token, []) if upload_token else []

    if not matched_students:
        return jsonify({'error': 'No matched students found. Please upload and process a file first.'}), 400
    
    # Filter students who have phone numbers
    students_with_phone = [s for s in matched_students if s.get('phone')]
    
    if not students_with_phone:
        return jsonify({'error': 'No students found with phone numbers in database.'}), 400
    
    # Generate unique session ID for this WhatsApp batch
    session_id = str(uuid.uuid4())
    whatsapp_sessions[session_id] = students_with_phone
    
    # Start background WhatsApp sending with PyWhatKit
    thread = threading.Thread(target=send_whatsapp_messages_background_pywhatkit, args=(students_with_phone, session_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'total_students': len(students_with_phone),
        'students_without_phone': len(matched_students) - len(students_with_phone)
    })

@app.route('/whatsapp_progress/<session_id>')
@login_required
def get_whatsapp_progress(session_id):
    if session_id in whatsapp_progress:
        return jsonify(whatsapp_progress[session_id])
    else:
        return jsonify({'error': 'Session not found'}), 404

@app.route('/cancel_whatsapp/<session_id>', methods=['POST'])
@login_required
def cancel_whatsapp(session_id):
    if session_id in whatsapp_progress:
        del whatsapp_progress[session_id]
    if session_id in whatsapp_sessions:
        del whatsapp_sessions[session_id]
    return jsonify({'success': True, 'message': 'WhatsApp sending cancelled'})

@app.route('/close_whatsapp', methods=['POST'])
@login_required
def close_whatsapp():
    global whatsapp_driver
    try:
        if whatsapp_driver:
            whatsapp_driver.quit()
            whatsapp_driver = None
        return jsonify({'success': True, 'message': 'WhatsApp browser closed'})
    except Exception as e:
        return jsonify({'error': f'Error closing WhatsApp browser: {str(e)}'}), 500

# =========================================================
# SEATING ARRANGEMENTS MANAGEMENT (ADMIN ONLY)
# =========================================================
@app.route('/api/arrangements', methods=['GET'])
@admin_required
def list_arrangements():
    """Lists all uploaded seating arrangements with their allocation status."""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('''
            SELECT id, filename, title, total_students, is_allocated, 
                   uploaded_at, allocated_at
            FROM seating_arrangements
            ORDER BY uploaded_at DESC;
        ''')
        rows = cur.fetchall()
        arrangements = []
        for r in rows:
            arrangements.append({
                'id': r['id'],
                'filename': r['filename'],
                'title': r['title'] or r['filename'],
                'total_students': r['total_students'],
                'is_allocated': bool(r['is_allocated']),
                'uploaded_at': r['uploaded_at'].strftime('%d %b %Y, %I:%M %p') if r['uploaded_at'] else '',
                'allocated_at': r['allocated_at'].strftime('%d %b %Y, %I:%M %p') if r['allocated_at'] else None
            })
        cur.close()
        conn.close()
        return jsonify({'success': True, 'arrangements': arrangements})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/arrangements/<int:arrangement_id>/allocate', methods=['POST'])
@admin_required
def allocate_arrangement(arrangement_id):
    """Allocates an uploaded seating arrangement to students so they can view it."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, filename, is_allocated FROM seating_arrangements WHERE id = %s;', (arrangement_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Seating arrangement not found.'}), 404

        cur.execute('''
            UPDATE seating_arrangements 
            SET is_allocated = TRUE, allocated_at = NOW() 
            WHERE id = %s;
        ''', (arrangement_id,))
        cur.execute('''
            UPDATE seating_allocations 
            SET is_allocated = TRUE 
            WHERE arrangement_id = %s;
        ''', (arrangement_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Seating arrangement "{row[1]}" allocated successfully! Students can now view their assigned seats.',
            'arrangement_id': arrangement_id,
            'is_allocated': True
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/arrangements/<int:arrangement_id>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete_arrangement(arrangement_id):
    """Deletes an uploaded seating arrangement and purges its seat allocations."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, filename FROM seating_arrangements WHERE id = %s;', (arrangement_id,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({'success': False, 'error': 'Seating arrangement not found.'}), 404

        filename = row[1]
        cur.execute('DELETE FROM seating_arrangements WHERE id = %s;', (arrangement_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Seating arrangement "{filename}" and its allocations were deleted successfully.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# =========================================================
# STUDENT PORTAL & PROFILE CONTROLLER
# =========================================================
@app.route('/student')
@student_required
def student_portal():
    """Renders the dedicated student dashboard with Seat Allotment & Profile."""
    student_id = session.get('student_id')
    conn = None
    student = None
    allocations = []

    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cur.fetchone()

        if student:
            # Query all active allocated seat records for this student across all allocated arrangements
            cur.execute("""
                SELECT sa.*, arr.filename as arrangement_filename, arr.title as arrangement_title, arr.allocated_at
                FROM seating_allocations sa
                JOIN seating_arrangements arr ON sa.arrangement_id = arr.id
                WHERE sa.enrollment_number = %s 
                  AND sa.is_allocated = TRUE 
                  AND arr.is_allocated = TRUE
                ORDER BY sa.date ASC, sa.time ASC, sa.id ASC;
            """, (student['enrollment_number'],))
            allocations = cur.fetchall()

        cur.close()
    except Exception as e:
        print(f"Error loading student portal: {e}")
    finally:
        if conn:
            conn.close()

    if not student:
        session.clear()
        return redirect(url_for('login'))

    has_custom_password = bool(student.get('password') and str(student['password']).strip())

    return render_template(
        'student.html',
        student=student,
        allocations=allocations,
        allocation=allocations[0] if allocations else None,
        has_custom_password=has_custom_password
    )

@app.route('/student/update-name', methods=['POST'])
@student_required
def student_update_name():
    """Allows student to update their displayed name in PostgreSQL."""
    data = request.get_json(silent=True) or {}
    new_name = (data.get('name') or request.form.get('name') or '').strip()

    if not new_name or len(new_name) < 2:
        return jsonify({'success': False, 'error': 'Please enter a valid student name (at least 2 characters).'}), 400

    student_id = session.get('student_id')
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE students SET name = %s WHERE id = %s", (new_name, student_id))

        # Also keep seating_allocations name in sync if an allotment exists
        enrollment = session.get('enrollment_number')
        if enrollment:
            cur.execute("UPDATE seating_allocations SET student_name = %s WHERE enrollment_number = %s", (new_name, enrollment))

        conn.commit()
        cur.close()

        session['student_name'] = new_name
        return jsonify({'success': True, 'message': 'Name updated successfully!', 'name': new_name})
    except Exception as e:
        print(f"Error updating student name: {e}")
        return jsonify({'success': False, 'error': 'Database error while updating name.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/student/change-password', methods=['POST'])
@student_required
def student_change_password():
    """Allows student to change their password, updating the password column in PostgreSQL."""
    data = request.get_json(silent=True) or {}
    current_password = (data.get('current_password') or request.form.get('current_password') or '').strip()
    new_password = (data.get('new_password') or request.form.get('new_password') or '').strip()
    confirm_password = (data.get('confirm_password') or request.form.get('confirm_password') or '').strip()

    if not current_password:
        return jsonify({'success': False, 'error': 'Please enter your current password.'}), 400
    if not new_password or len(new_password) < 4:
        return jsonify({'success': False, 'error': 'New password must be at least 4 characters long.'}), 400
    if new_password != confirm_password:
        return jsonify({'success': False, 'error': 'New password and confirmation do not match.'}), 400

    student_id = session.get('student_id')
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        student = cur.fetchone()

        if not student:
            cur.close()
            return jsonify({'success': False, 'error': 'Student account not found.'}), 404

        # Validate current password
        db_pwd = student.get('password')
        expected_current = db_pwd if (db_pwd and str(db_pwd).strip()) else str(student['enrollment_number']).strip()

        if current_password != expected_current:
            cur.close()
            return jsonify({
                'success': False,
                'error': 'Current password is incorrect. (Note: Your default initial password is your 12-digit enrollment number).'
            }), 400

        # Update password in database
        cur.execute("UPDATE students SET password = %s WHERE id = %s", (new_password, student_id))
        conn.commit()
        cur.close()

        return jsonify({
            'success': True,
            'message': 'Password changed successfully! Please use your new password for all future logins.'
        })
    except Exception as e:
        print(f"Error changing student password: {e}")
        return jsonify({'success': False, 'error': 'Database error while changing password.'}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Disable reloader to prevent background threads from being killed
    app.run(debug=True, use_reloader=False)