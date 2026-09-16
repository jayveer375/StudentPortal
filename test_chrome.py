#!/usr/bin/env python3
"""
Test script to check Chrome and ChromeDriver setup
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import time

def test_chrome_basic():
    print("🧪 Testing basic Chrome setup...")
    
    try:
        # Basic Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")  # Run headless for testing
        
        # Try ChromeDriverManager
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ ChromeDriverManager works!")
        except Exception as e1:
            print(f"❌ ChromeDriverManager failed: {e1}")
            try:
                # Try system ChromeDriver
                driver = webdriver.Chrome(options=chrome_options)
                print("✅ System ChromeDriver works!")
            except Exception as e2:
                print(f"❌ System ChromeDriver failed: {e2}")
                return False
        
        # Test basic navigation
        driver.get("https://www.google.com")
        print(f"✅ Successfully navigated to Google")
        print(f"Page title: {driver.title}")
        
        # Clean up
        driver.quit()
        print("✅ Chrome test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Chrome test failed: {e}")
        return False

def test_chrome_whatsapp():
    print("\n🧪 Testing Chrome for WhatsApp Web...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Create temp user data directory
        user_data_dir = os.path.join(os.getcwd(), "temp_test_profile")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ Chrome started for WhatsApp test")
        
        # Try to open WhatsApp Web
        print("Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        # Wait a bit and check if page loaded
        time.sleep(5)
        page_title = driver.title
        print(f"Page title: {page_title}")
        
        if "WhatsApp" in page_title:
            print("✅ WhatsApp Web loaded successfully!")
            print("Note: QR code should be visible (if not logged in)")
        else:
            print(f"⚠️ Unexpected page title: {page_title}")
        
        # Keep browser open for 10 seconds for manual inspection
        print("Keeping browser open for 10 seconds for inspection...")
        time.sleep(10)
        
        driver.quit()
        
        # Clean up temp directory
        import shutil
        if os.path.exists(user_data_dir):
            try:
                shutil.rmtree(user_data_dir)
            except:
                pass
                
        print("✅ WhatsApp Web test completed!")
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp Web test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Chrome and WhatsApp Web Compatibility Test")
    print("=" * 50)
    
    # Test basic Chrome
    basic_ok = test_chrome_basic()
    
    if basic_ok:
        # Test WhatsApp specific setup
        whatsapp_ok = test_chrome_whatsapp()
        
        if whatsapp_ok:
            print("\n🎉 All tests passed! Chrome and WhatsApp Web should work.")
        else:
            print("\n⚠️ Basic Chrome works, but WhatsApp Web has issues.")
    else:
        print("\n❌ Basic Chrome setup has problems.")
    
    print("=" * 50)