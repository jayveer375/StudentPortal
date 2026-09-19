"""
Hall Ticket & Seating Allotment Receipt PDF Generator
Generates high-quality, printable vector PDF receipts for students
with dynamic enrollment, college code, subject codes, classrooms, blocks,
and scannable verification QR code.
"""

import io
import datetime
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def extract_college_code(enrollment_number, college_name=""):
    """
    Extracts GTU college code from 12-digit enrollment number (digits 3-5).
    Example: 246171063001 -> '617' (Government Polytechnic Ahmedabad)
    """
    enr_str = str(enrollment_number or '').strip()
    if len(enr_str) == 12 and enr_str[2:5].isdigit():
        return enr_str[2:5]
    if "Government Polytechnic Ahmedabad" in str(college_name):
        return "617"
    return "617"


def generate_qr_code_image(qr_text, size=80):
    """Generates a QR Code image in memory as BytesIO for ReportLab Image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    return img_buffer


def generate_hall_ticket_pdf(student, allocations, specific_alloc_id=None):
    """
    Builds and returns an in-memory PDF (BytesIO) of the student's
    official Examination Hall Ticket & Seating Allotment Receipt.
    """
    buffer = io.BytesIO()

    # Document setup: A4, better margins for cleaner look
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=42,
        rightMargin=42,
        topMargin=38,
        bottomMargin=38
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    primary_color = colors.HexColor("#1E3A8A")   # Deep University Blue
    dark_slate = colors.HexColor("#0F172A")      # Text Dark
    border_color = colors.HexColor("#CBD5E1")    # Subtle Slate Border
    table_header_bg = colors.HexColor("#1E3A8A") # Table Header Navy
    light_row_bg = colors.HexColor("#F8FAFC")    # Row alternate

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        alignment=TA_CENTER,
        textColor=primary_color,
        spaceAfter=4
    )

    sub_title_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=dark_slate,
        spaceAfter=4
    )

    meta_header_style = ParagraphStyle(
        'MetaHeader',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#475569")
    )

    badge_title_style = ParagraphStyle(
        'BadgeTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    info_label_style = ParagraphStyle(
        'InfoLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    )

    info_val_style = ParagraphStyle(
        'InfoVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=12,
        textColor=dark_slate
    )

    mono_val_style = ParagraphStyle(
        'MonoVal',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=10,
        leading=12,
        textColor=dark_slate
    )

    table_th_style = ParagraphStyle(
        'TableTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    table_td_style = ParagraphStyle(
        'TableTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=dark_slate
    )

    table_td_center = ParagraphStyle(
        'TableTDCenter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=dark_slate
    )

    table_td_bold_center = ParagraphStyle(
        'TableTDBoldCenter',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        alignment=TA_CENTER,
        textColor=primary_color
    )

    instruction_style = ParagraphStyle(
        'Instructions',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor("#334155"),
        alignment=TA_LEFT
    )

    instruction_title = ParagraphStyle(
        'InstructionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=primary_color
    )

    story = []

    # Filter allocations if specific allocation requested
    target_allocs = allocations
    if specific_alloc_id:
        target_allocs = [a for a in allocations if str(a.get('id')) == str(specific_alloc_id)]
        if not target_allocs:
            target_allocs = allocations

    student_name = student.get('name', 'Student')
    enrollment = str(student.get('enrollment_number', 'N/A'))
    college_name = student.get('college_name', 'Government Polytechnic Ahmedabad')
    college_code = extract_college_code(enrollment, college_name)
    branch = student.get('branch', 'Computer Engineering')
    semester = f"SEM {student.get('semester', '4')}"
    email = student.get('email', '')
    now_str = datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
    receipt_no = f"GTU-HT-{enrollment}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}"

    # -------------------------------------------------------------
    # 1. INSTITUTION & UNIVERSITY HEADER BLOCK
    # -------------------------------------------------------------
    header_data = [
        [
            Paragraph(college_name.upper(), title_style)
        ],
        [
            Paragraph("AFFILIATED TO GUJARAT TECHNOLOGICAL UNIVERSITY (GTU)", sub_title_style)
        ],
        [
            Paragraph("EXAMINATION HALL TICKET & SEATING ALLOTMENT RECEIPT", meta_header_style)
        ]
    ]

    header_table = Table(header_data, colWidths=[515])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # Colored Hall Ticket Bar
    bar_data = [[
        Paragraph(f"OFFICIAL HALL TICKET &bull; SUMMER/WINTER EXAMINATION 2026 &bull; RECEIPT NO: {receipt_no}", badge_title_style)
    ]]
    bar_table = Table(bar_data, colWidths=[515], rowHeights=[24])
    bar_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(bar_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 2. STUDENT INFORMATION & QR VERIFICATION GRID
    # -------------------------------------------------------------
    # Generate verification QR Code
    first_subject = target_allocs[0].get('subject', 'General') if target_allocs else 'N/A'
    first_room = target_allocs[0].get('room', 'TBA') if target_allocs else 'TBA'
    first_block = target_allocs[0].get('block', 'TBA') if target_allocs else 'TBA'

    qr_text = (
        f"GTU-EXAM-VERIFIED|ENR:{enrollment}|NAME:{student_name}|COLLEGE:{college_code}|"
        f"ROOM:{first_room}|BLOCK:{first_block}|SUBJECT:{first_subject}|RECEIPT:{receipt_no}"
    )
    qr_img_buffer = generate_qr_code_image(qr_text, size=70)
    qr_flowable = Image(qr_img_buffer, width=68, height=68)

    # 4-column student details + 1 column for QR verification
    student_details_data = [
        [
            Paragraph("Candidate Name:", info_label_style),
            Paragraph(student_name.upper(), info_val_style),
            Paragraph("Enrollment Number:", info_label_style),
            Paragraph(enrollment, mono_val_style),
            qr_flowable
        ],
        [
            Paragraph("Institute Name:", info_label_style),
            Paragraph(college_name, info_val_style),
            Paragraph("Institute Code:", info_label_style),
            Paragraph(college_code, mono_val_style),
            "" # span with QR
        ],
        [
            Paragraph("Program / Branch:", info_label_style),
            Paragraph(branch, info_val_style),
            Paragraph("Current Semester:", info_label_style),
            Paragraph(semester, info_val_style),
            "" # span with QR
        ],
        [
            Paragraph("Registered Email:", info_label_style),
            Paragraph(email, info_val_style),
            Paragraph("Generated On:", info_label_style),
            Paragraph(now_str, info_val_style),
            "" # span with QR
        ]
    ]

    # col widths: [100, 150, 100, 95, 78] -> Total = 523
    student_table = Table(
        student_details_data,
        colWidths=[100, 150, 100, 95, 78],
        rowHeights=[18, 18, 18, 18]
    )
    student_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.8, border_color),
        ('INNERGRID', (0, 0), (3, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('SPAN', (4, 0), (4, 3)), # span QR code across all 4 rows
        ('ALIGN', (4, 0), (4, 3), 'CENTER'),
        ('VALIGN', (4, 0), (4, 3), 'MIDDLE'),
        ('VALIGN', (0, 0), (3, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (4, 0), (4, 3), colors.HexColor("#FFFFFF")),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(student_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 3. SEATING ALLOTMENT TIMETABLE
    # -------------------------------------------------------------
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=primary_color,
        spaceAfter=4
    )
    story.append(Paragraph("ALLOCATED SEATING ARRANGEMENT & EXAM SCHEDULE", section_heading))

    table_rows = [
        [
            Paragraph("Sr.", table_th_style),
            Paragraph("Subject Code", table_th_style),
            Paragraph("Exam Date", table_th_style),
            Paragraph("Exam Timing", table_th_style),
            Paragraph("Allocated Classroom", table_th_style),
            Paragraph("Assigned Block", table_th_style),
            Paragraph("Invigilator Initial", table_th_style),
        ]
    ]

    # col widths: [28, 85, 75, 115, 80, 60, 80] = 523
    for idx, alloc in enumerate(target_allocs, start=1):
        subj = alloc.get('subject') or 'General Paper'
        date_str = alloc.get('date') or 'Scheduled Exam'
        time_str = alloc.get('time') or '10:30 AM TO 1:00 PM'
        room_str = alloc.get('room') or 'TBA'
        block_str = str(alloc.get('block') or '1')

        table_rows.append([
            Paragraph(str(idx), table_td_center),
            Paragraph(subj, table_td_bold_center),
            Paragraph(date_str, table_td_center),
            Paragraph(time_str, table_td_center),
            Paragraph(room_str, table_td_bold_center),
            Paragraph(block_str, table_td_bold_center),
            Paragraph("", table_td_center), # Signature box for exam supervisor
        ])

    alloc_table = Table(table_rows, colWidths=[28, 85, 75, 115, 80, 60, 80])
    
    table_style_list = [
        ('BACKGROUND', (0, 0), (-1, 0), table_header_bg),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.8, primary_color),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, border_color),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]

    # Alternate row colors
    for r in range(1, len(table_rows)):
        if r % 2 == 0:
            table_style_list.append(('BACKGROUND', (0, r), (-1, r), light_row_bg))
        else:
            table_style_list.append(('BACKGROUND', (0, r), (-1, r), colors.white))

    alloc_table.setStyle(TableStyle(table_style_list))
    story.append(alloc_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 4. CANDIDATE INSTRUCTIONS & CONDUCT CODE
    # -------------------------------------------------------------
    story.append(Paragraph("IMPORTANT CANDIDATE INSTRUCTIONS:", instruction_title))
    instructions = [
        "1. Candidate must report to their assigned <b>Classroom and Block at least 15 minutes before</b> the scheduled exam commencement.",
        "2. This Hall Ticket Receipt and a valid <b>Institute Identity Card</b> must be presented for inspection at the examination hall.",
        "3. Mobile phones, smart watches, digital gadgets, study notes, or programmable devices are <b>strictly forbidden</b> inside the examination hall.",
        "4. Verify that the <b>Subject Code</b> printed on your question paper matches the subject code allocated above.",
        "5. Occupy only the seat allocated against your enrollment number. Discrepancies should be reported immediately to the Examination Incharge.",
        "6. Any attempt of malpractice or breach of discipline will be prosecuted under GTU Unfair Means (UFM) regulations."
    ]

    instruction_data = []
    for inst in instructions:
        instruction_data.append([Paragraph(inst, instruction_style)])

    inst_table = Table(instruction_data, colWidths=[523])
    inst_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(inst_table)
    story.append(Spacer(1, 10))

    # -------------------------------------------------------------
    # 5. ATTESTATION & SIGNATURE BLOCKS
    # -------------------------------------------------------------
    sig_label_style = ParagraphStyle(
        'SigLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#334155")
    )

    signatures_data = [
        [
            Paragraph("____________________________<br/><b>Candidate's Signature</b><br/><font color='#64748B'>To be signed in presence of Invigilator</font>", sig_label_style),
            Paragraph("____________________________<br/><b>Invigilator's Signature</b><br/><font color='#64748B'>Verified Classroom & Block Allotment</font>", sig_label_style),
            Paragraph("____________________________<br/><b>Controller of Examinations</b><br/><font color='#64748B'>GTU Center Superintendent & Seal</font>", sig_label_style),
        ]
    ]

    sig_table = Table(signatures_data, colWidths=[174, 175, 174], rowHeights=[45])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 4))

    # Security footer line
    footer_text = Paragraph(
        f"<font size='6.5' color='#94A3B8'>System Generated Document &bull; GTU ExamDesk Seating System &bull; Verification Hash: {receipt_no} &bull; Valid for Session 2026</font>",
        ParagraphStyle('FooterNotice', parent=styles['Normal'], alignment=TA_CENTER)
    )
    story.append(footer_text)

    # Build the document
    doc.build(story)
    buffer.seek(0)
    return buffer
