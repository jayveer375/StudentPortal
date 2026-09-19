import requests
import fitz  # PyMuPDF

def test_student_flow():
    session = requests.Session()
    base_url = "http://127.0.0.1:5000"

    print("1. Testing Student Login...")
    # Jayveer Vora: email jayveervora47@gmail.com, password is jayveer@123
    login_resp = session.post(f"{base_url}/login", json={
        "username": "jayveervora47@gmail.com",
        "password": "jayveer@123"
    })
    print(f"Login status: {login_resp.status_code}, json: {login_resp.json()}")
    assert login_resp.status_code == 200, "Login failed"
    assert login_resp.json().get("success") is True, "Login response was not successful"

    print("\n2. Testing Student Portal Dashboard Page...")
    portal_resp = session.get(f"{base_url}/student")
    assert portal_resp.status_code == 200, f"Portal returned {portal_resp.status_code}"
    html = portal_resp.text
    
    # Check Table View & View Switcher elements
    assert "btnViewCards" in html, "btnViewCards missing from portal HTML"
    assert "btnViewTable" in html, "btnViewTable missing from portal HTML"
    assert "allotmentCardsView" in html, "allotmentCardsView missing from portal HTML"
    assert "allotmentTableView" in html, "allotmentTableView missing from portal HTML"
    assert "studentAllotmentTable" in html, "studentAllotmentTable missing from portal HTML"
    assert "Download Hall Ticket (PDF)" in html, "Download Hall Ticket button text missing"
    assert "41046307" in html, "Subject code 41046307 missing from student portal"
    assert "1A110" in html, "Classroom 1A110 missing from student portal"
    print("All Table View & Toolbar elements verified in HTML successfully!")

    print("\n3. Testing Dynamic PDF Hall Ticket Download...")
    download_resp = session.get(f"{base_url}/student/download-hall-ticket")
    assert download_resp.status_code == 200, f"Download returned {download_resp.status_code}"
    assert "application/pdf" in download_resp.headers.get("Content-Type", ""), "Content-Type is not PDF"
    assert download_resp.content.startswith(b"%PDF-"), "Response does not start with PDF magic bytes"
    print(f"Hall ticket PDF downloaded successfully! Size: {len(download_resp.content)} bytes")

    # Read and verify contents of the PDF using PyMuPDF
    doc = fitz.open(stream=download_resp.content, filetype="pdf")
    print(f"PDF page count: {len(doc)}")
    full_pdf_text = ""
    for page in doc:
        full_pdf_text += page.get_text()

    print("--- Extracted PDF Text Preview ---")
    print(full_pdf_text[:500])
    print("---------------------------------")

    # Verify key details in Hall Ticket PDF
    assert "JAYVEER VORA" in full_pdf_text.upper(), "Student name missing from PDF"
    assert "246171063001" in full_pdf_text, "Enrollment number missing from PDF"
    assert "617" in full_pdf_text, "Institute code 617 missing from PDF"
    assert "GOVERNMENT POLYTECHNIC AHMEDABAD" in full_pdf_text.upper(), "Institute name missing from PDF"
    assert "41046307" in full_pdf_text, "Subject code 41046307 missing from PDF"
    assert "1A110" in full_pdf_text, "Room 1A110 missing from PDF"
    assert "HALL TICKET" in full_pdf_text.upper(), "HALL TICKET missing from PDF"
    print("All required dynamic data points confirmed inside the generated Hall Ticket PDF!")

    print("\n4. Testing Per-Allocation Hall Ticket Download...")
    single_resp = session.get(f"{base_url}/student/download-hall-ticket?allocation_id=704")
    assert single_resp.status_code == 200
    assert single_resp.content.startswith(b"%PDF-")
    print("Per-allocation download verified successfully!")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_student_flow()
