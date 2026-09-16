#!/usr/bin/env python3
"""
Test PyWhatKit WhatsApp functionality
"""

import pywhatkit as pwk
import datetime
import time

def test_pywhatkit():
    print("🧪 Testing PyWhatKit WhatsApp functionality...")
    
    # Test phone numbers from your database
    phone1 = "+919512108880"  # Jayveer
    phone2 = "+919737408880"  # Aarav Patwa
    
    message = """🎓 *Test Exam Notification*

Dear Student,

This is a test message from the Exam Seating System.

📝 *Subject:* Network Programming  
📅 *Date:* 12 Sept 2026
⏰ *Time:* 10:30 AM - 1:00 PM

📍 *Location:*
🏢 Block: 1
🚪 Room: 1A110

- Government Polytechnic Ahmedabad"""

    try:
        print(f"Preparing to send WhatsApp to {phone1}")
        
        # Get current time and add 2 minutes for sending
        now = datetime.datetime.now()
        send_time = now + datetime.timedelta(minutes=2)
        
        print(f"Current time: {now.strftime('%H:%M')}")
        print(f"Message will be sent at: {send_time.strftime('%H:%M')}")
        print(f"Please ensure WhatsApp Web is logged in on your default browser")
        print(f"The browser will open automatically in about 1 minute...")
        
        # Send message using PyWhatKit
        pwk.sendwhatmsg(
            phone_no=phone1,
            message=message,
            time_hour=send_time.hour,
            time_min=send_time.minute,
            wait_time=15,  # Wait 15 seconds after opening WhatsApp Web
            tab_close=True  # Close tab after sending
        )
        
        print("✅ PyWhatKit message sending completed!")
        print("Check your WhatsApp to verify the message was sent")
        
        return True
        
    except Exception as e:
        print(f"❌ PyWhatKit test failed: {e}")
        return False

if __name__ == "__main__":
    print("📱 PyWhatKit WhatsApp Test")
    print("=" * 40)
    print("This will send a test message to 9512108880")
    print("Make sure:")
    print("1. You're logged into WhatsApp Web on your default browser")
    print("2. The phone number is correct")
    print("3. Don't close the browser when it opens")
    print("=" * 40)
    
    # Ask for confirmation
    confirm = input("Do you want to proceed with the test? (y/n): ")
    
    if confirm.lower() == 'y':
        success = test_pywhatkit()
        if success:
            print("\n🎉 Test completed! Check WhatsApp for the message.")
        else:
            print("\n❌ Test failed. Check the error messages above.")
    else:
        print("Test cancelled.")