import os
import requests
import openpyxl

BASE_URL = 'http://127.0.0.1:5000'

def create_second_arrangement_excel(filename="test_second_arrangement.xlsx"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Seating"

    # Title and schedule metadata
    ws.append(["GOVERNMENT POLYTECHNIC AHMEDABAD"])
    ws.append(["EXAM SEATING ARRANGEMENT - AFTERNOON SESSION"])
    ws.append(["Date: 15/09/2026"])
    ws.append(["Time: 02:00 PM TO 04:30 PM"])
    ws.append([])

    # Header row
    ws.append(["Subject Code", "Room No", "Block", "Semester", "Student Seat No"])

    # Student 246171063001 assigned to a second class (Room 205, Block 2B205)
    ws.append(["3340702 - Operating Systems", "Room 205", "2B205", "SEM 4", "246171063001"])
    ws.append(["3340702 - Operating Systems", "Room 205", "2B205", "SEM 4", "246171063003"])

    wb.save(filename)
    return filename

def run_tests():
    print("[START] Running Multi-Seating Arrangements & Explicit Allocation Test Suite...")

    session_admin = requests.Session()
    session_student = requests.Session()

    # 1. Admin Login
    res = session_admin.post(f"{BASE_URL}/login", json={'username': 'Admin@gmail.com', 'password': 'admin@123'})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    assert res.json().get('success') == True
    print("1. Admin authenticated successfully.")

    # 2. Test GET /api/arrangements
    res = session_admin.get(f"{BASE_URL}/api/arrangements")
    assert res.status_code == 200, f"GET /api/arrangements failed: {res.text}"
    arrangements = res.json().get('arrangements', [])
    print(f"2. Current arrangements in DB: {len(arrangements)}")

    # Ensure at least one allocated arrangement exists for initial baseline
    if arrangements:
        for arr in arrangements:
            if not arr['is_allocated']:
                print(f"   Allocating baseline arrangement ID {arr['id']} ('{arr['filename']}')...")
                res = session_admin.post(f"{BASE_URL}/api/arrangements/{arr['id']}/allocate")
                assert res.status_code == 200
                assert res.json().get('success') == True

    # 3. Student Login
    res = session_student.post(f"{BASE_URL}/login", json={'username': 'jayveervora47@gmail.com', 'password': '246171063001'})
    assert res.status_code == 200, f"Student login failed: {res.text}"
    print("3. Student authenticated successfully.")

    # 4. Check initial student portal (should see initial baseline allocation, but not Room 205)
    res = session_student.get(f"{BASE_URL}/student")
    assert res.status_code == 200
    initial_html = res.text
    assert "Room 205" not in initial_html
    assert "Seating Confirmed" in initial_html
    print("4. Student initially sees baseline allocation (Room 205 is not present).")

    # 5. Create and Upload Second Seating File
    excel_file = create_second_arrangement_excel()
    with open(excel_file, 'rb') as f:
        res = session_admin.post(f"{BASE_URL}/upload", files={'pdf_file': (excel_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
    assert res.status_code == 200, f"Upload failed: {res.text}"
    upload_res = res.json()
    assert upload_res.get('success') == True
    assert upload_res.get('is_allocated') == False, "Uploaded file must be pending (is_allocated=False)"
    new_arr_id = upload_res.get('arrangement_id')
    assert new_arr_id is not None
    print(f"5. Uploaded second arrangement (ID: {new_arr_id}). is_allocated: {upload_res.get('is_allocated')} (Pending).")

    # 6. Verify Gatekeeping: Student must NOT see the unallocated arrangement
    res = session_student.get(f"{BASE_URL}/student")
    assert res.status_code == 200
    student_html_pending = res.text
    assert "Room 205" not in student_html_pending, "CRITICAL ERROR: Student can see unallocated arrangement before admin approval!"
    print("6. Gatekeeping confirmed: Unallocated arrangement (Room 205) is NOT visible to student.")

    # 7. Admin Allocates the Arrangement
    res = session_admin.post(f"{BASE_URL}/api/arrangements/{new_arr_id}/allocate")
    assert res.status_code == 200, f"Allocation failed: {res.text}"
    allocate_res = res.json()
    assert allocate_res.get('success') == True
    assert allocate_res.get('is_allocated') == True
    print(f"7. Admin allocated arrangement ID {new_arr_id} successfully.")

    # 8. Verify Student Portal: Student now sees BOTH allocations!
    res = session_student.get(f"{BASE_URL}/student")
    assert res.status_code == 200
    student_html_multi = res.text
    assert "Room 205" in student_html_multi or "205" in student_html_multi, "New Room 205 missing!"
    assert "Class #1" in student_html_multi
    assert "Class #2" in student_html_multi
    assert "Operating Systems" in student_html_multi
    assert "Multiple Class Allocations" in student_html_multi
    print("8. Multi-arrangement verified: Student successfully sees BOTH classes (Class #1 & Class #2 / Room 205).")

    # 9. Admin Deletes the Second Arrangement
    res = session_admin.post(f"{BASE_URL}/api/arrangements/{new_arr_id}/delete")
    assert res.status_code == 200, f"Delete failed: {res.text}"
    delete_res = res.json()
    assert delete_res.get('success') == True
    print(f"9. Admin deleted arrangement ID {new_arr_id} successfully.")

    # 10. Verify Student Portal after deletion: Room 205 is cleanly removed
    res = session_student.get(f"{BASE_URL}/student")
    assert res.status_code == 200
    student_html_after_delete = res.text
    assert "Room 205" not in student_html_after_delete
    assert "Seating Confirmed" in student_html_after_delete
    print("10. Deletion verified: Student now only sees remaining baseline class.")

    # Cleanup local test file
    if os.path.exists(excel_file):
        os.remove(excel_file)
    print("11. Cleaned up temporary test file.")

    print("\n[SUCCESS] ALL 11 AUTOMATED VERIFICATION TESTS PASSED WITH 100% SUCCESS!")

if __name__ == '__main__':
    run_tests()
