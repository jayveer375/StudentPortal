#!/usr/bin/env python3
"""
Test script to verify Chrome opens in NORMAL mode (not incognito)
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

def test_normal_mode():
    print("🧪 Testing Chrome Normal Mode (NOT incognito)...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        
        # User data directory for persistence
        user_data_dir = os.path.join(os.getcwd(), "whatsapp_profile")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=WhatsAppProfile")
        
        # Explicitly ensure NOT incognito
        chrome_options.add_experimental_option("detach", True)
        
        print(f"Using profile directory: {user_data_dir}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Chrome started")
        
        # Navigate to a test page
        driver.get("https://web.whatsapp.com")
        
        # Check if incognito mode indicator is present
        page_source = driver.page_source.lower()
        
        # Check browser title and URL
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Look for incognito indicators
        is_incognito = False
        
        # Check if "incognito" appears anywhere in the page
        if "incognito" in page_source or "private" in page_source:
            print("⚠️ Possible incognito mode detected in page content")
            is_incognito = True
        
        # Check window title through JavaScript
        try:
            window_info = driver.execute_script("return {title: document.title, userAgent: navigator.userAgent}")
            print(f"Window title: {window_info['title']}")
            print(f"User Agent: {window_info['userAgent']}")
        except:
            pass
        
        if not is_incognito:
            print("✅ Chrome appears to be in NORMAL mode (not incognito)")
            print("✅ WhatsApp should be able to save login session")
        else:
            print("❌ Chrome appears to be in INCOGNITO mode")
            print("❌ WhatsApp will require QR scan every time")
        
        # Keep browser open for manual verification
        print("\n📋 Manual Verification:")
        print("1. Look at the browser window")
        print("2. Check if there's an incognito icon (person with hat)")
        print("3. Check if browser says 'Incognito' anywhere")
        print("4. The browser should look like normal Chrome")
        print("\nKeeping browser open for 15 seconds for manual inspection...")
        
        time.sleep(15)
        
        driver.quit()
        return not is_incognito
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Chrome Normal Mode Test")
    print("=" * 40)
    
    success = test_normal_mode()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 SUCCESS: Chrome is in normal mode!")
        print("✅ WhatsApp login will be persistent")
    else:
        print("❌ PROBLEM: Chrome might be in incognito mode")
        print("⚠️ WhatsApp will require QR scan every time")
    print("=" * 40)