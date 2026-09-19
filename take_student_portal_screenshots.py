import os
import time
import requests
import fitz  # PyMuPDF
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

artifact_dir = r"C:\Users\ADMIN\.gemini\antigravity-ide\brain\4b198ae3-cf23-4fdc-934a-68cb04925c54"
os.makedirs(artifact_dir, exist_ok=True)

# 1. Render PDF Hall ticket to image using PyMuPDF
print("Rendering PDF Hall Ticket to image...")
session = requests.Session()
login_res = session.post("http://127.0.0.1:5000/login", json={
    "username": "jayveervora47@gmail.com",
    "password": "jayveer@123"
})
if login_res.status_code == 200:
    pdf_res = session.get("http://127.0.0.1:5000/student/download-hall-ticket")
    if pdf_res.status_code == 200 and pdf_res.content.startswith(b"%PDF-"):
        doc = fitz.open(stream=pdf_res.content, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        pdf_img_path = os.path.join(artifact_dir, "hall_ticket_receipt.png")
        pix.save(pdf_img_path)
        print(f"[OK] Hall ticket PDF preview image saved: {pdf_img_path}")

# 2. Capture UI Screenshots using Selenium Headless Chrome with injected session cookie
print("Capturing Student Portal UI screenshots...")
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1280,960")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # First navigate to domain so cookies can be set
    driver.get("http://127.0.0.1:5000/login")
    time.sleep(0.5)
    
    # Inject Flask session cookie from requests
    for cookie in session.cookies:
        driver.add_cookie({
            'name': cookie.name,
            'value': cookie.value,
            'path': cookie.path or '/'
        })
        
    # Navigate directly to student portal
    driver.get("http://127.0.0.1:5000/student")
    time.sleep(1)
    print(f"Current URL: {driver.current_url}")
    
    # Capture Card View
    card_img_path = os.path.join(artifact_dir, "student_card_view.png")
    driver.save_screenshot(card_img_path)
    print(f"[OK] Card View screenshot saved: {card_img_path}")
    
    # Switch to Table View
    btn_table = driver.find_element(By.ID, "btnViewTable")
    btn_table.click()
    time.sleep(0.8)
    
    # Capture Table View
    table_img_path = os.path.join(artifact_dir, "student_table_view.png")
    driver.save_screenshot(table_img_path)
    print(f"[OK] Table View screenshot saved: {table_img_path}")

finally:
    driver.quit()

print("Screenshot capture completed successfully!")
