# Install: pip install selenium webdriver-manager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import time
import os
from datetime import datetime
from urllib.parse import quote_plus
# ============================================
# EDIT THESE SETTINGS
# ============================================

# Path to your Firedragon browser (edit this to match your system)
# Common locations:
# Linux: "/usr/bin/firedragon" or "/usr/lib/firedragon/firedragon"
# Windows: "C:\\Program Files\\Firedragon\\firedragon.exe"
# If you're using regular Firefox instead, use: "/usr/bin/firefox"
BROWSER_PATH = "/usr/bin/firedragon"

# How long to wait between messages (in seconds)
DELAY_BETWEEN_MESSAGES = 15

# Your phone numbers (with country code)
PHONE_NUMBERS = [
    +201030783589,
    +201223944772,
    +201065765379,
    +201012813959,
    +201126534319,
    +201013108212,
    +249124035850,
    +201111309841,
    +201055903512,
    +201157688684,
    +201100732370,
    +201128948531,
    +201558782590,
    +201113638541,
    +201158857766,
    +201207184277,
    +201064947323,
    +201127678210,
    +201220952829,
    +201070326462,
    +201017635248,
    +201014291137,
    +201282025093,
    +201025217601,
    +201285114000,
    +201094700490,
    +201033638711,
    +201283468422,
    +201099556793,
    +201011326327,
    +201143700150,
    +966568957025,
    +201289364411,
    +201102147945,
    +201150613806,
    +201151523297,
    +201031795155,
    +201128904863,
    +201223783198,
    +201030741871,
    +201221352872,
    +201008735542,
    +201015405748,
    +201006532898,
    +201557051217,
    +213556857725,
    +201143024013,
    +201221637676,
    +201119169321,
    +201099104206,
    +201206612032,
    +201158583351,
    +201155686430
]
  # Your message
message_text = """


"""

MESSAGE = quote_plus(message_text)
# ============================================
# DON'T EDIT BELOW THIS LINE
# ============================================

# Create log file
LOG_FILE = f"whatsapp_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def write_log(message):
    """Write a message to both console and log file"""
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def open_whatsapp():
    """Open WhatsApp Web in Firefox/Firedragon"""
    print("Opening WhatsApp Web...")
    
    # Setup Firefox/Firedragon options
    options = Options()
    
    # Check if browser path exists
    BROWSER_PATH = "/usr/bin/firedragon"  # Change this to your actual path
    if os.path.exists(BROWSER_PATH):
        options.binary_location = BROWSER_PATH
        print(f"Using browser: {BROWSER_PATH}")
    else:
        print(f"⚠️  Warning: Browser not found at {BROWSER_PATH}")
        print("Trying default Firefox location...")
    
    # Create driver
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.get("https://web.whatsapp.com")
    
    print("\nPlease scan the QR code with your phone")
    print("Waiting 30 seconds for you to login...")
    time.sleep(60)
    
    return driver

def send_message(driver, phone, message=MESSAGE):
    """Send a message to one phone number"""
    try:
        # Open chat with this number
        url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
        print(url)
        driver.get(url)
        time.sleep(15)
        
        # Find the message box
        message_box = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        
        # Type the message (line by line to keep formatting)
        #lines = message.split('\n')
        #for i, line in enumerate(lines):
        #    message_box.send_keys(line)
        #    if i < len(lines) - 1:
        #        message_box.send_keys(Keys.SHIFT + Keys.ENTER)
        
        # Send the message
        time.sleep(2)
        message_box.send_keys(Keys.ENTER)
        
        print(f"✓ Sent to {phone}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to send to {phone}: {e}")
        return False

def main():
    """Main function - runs everything"""
    write_log("="*50)
    write_log("WhatsApp Bulk Sender - Starting")
    write_log("="*50)
    write_log(f"Total numbers: {len(PHONE_NUMBERS)}")
    write_log(f"Delay between messages: {DELAY_BETWEEN_MESSAGES} seconds")
    write_log(f"Log file: {LOG_FILE}")
    write_log("="*50)
    
    # Ask user to confirm
    response = input("\nStart sending? (y/n): ").lower()
    if response != 'y':
        write_log("❌ CANCELLED by user")
        return
    
    write_log("✓ User confirmed - Starting process...")
    start_time = datetime.now()
    write_log(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Open WhatsApp
    driver = open_whatsapp()
    
    # Send to each number
    success_count = 0
    fail_count = 0
    failed_numbers = []
    
    for i, phone in enumerate(PHONE_NUMBERS, 1):
        write_log(f"\n[{i}/{len(PHONE_NUMBERS)}] Processing: {phone}")
        
        if send_message(driver, phone):
            success_count += 1
        else:
            fail_count += 1
            failed_numbers.append(phone)
        
        # Wait before next message (except for last one)
        if i < len(PHONE_NUMBERS):
            write_log(f"⏸️  Waiting {DELAY_BETWEEN_MESSAGES} seconds...")
            time.sleep(DELAY_BETWEEN_MESSAGES)
    
    # Calculate duration
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Show results
    write_log("\n" + "="*50)
    write_log("FINAL REPORT")
    write_log("="*50)
    write_log(f"✓ Successful: {success_count}")
    write_log(f"✗ Failed: {fail_count}")
    write_log(f"📊 Success Rate: {(success_count/len(PHONE_NUMBERS)*100):.1f}%")
    write_log(f"⏱️  Duration: {duration}")
    write_log(f"🕐 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed_numbers:
        write_log("\n❌ Failed Numbers List:")
        for phone in failed_numbers:
            write_log(f"   • {phone}")
    
    write_log("="*50)
    write_log(f"📄 Full log saved to: {LOG_FILE}")
    write_log("="*50)
    
    # Keep browser open for 10 seconds
    write_log("\nClosing browser in 10 seconds...")
    time.sleep(10)
    driver.quit()
    write_log("✓ Browser closed - Process complete!")

# Run the script
if __name__ == "__main__":
    main()
