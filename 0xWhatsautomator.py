"""
0xWhatsautomator - Playwright edition
Install:  pip install playwright
Then either:
  playwright install chromium      # downloads Playwright's bundled Chromium
or, to drive your actual installed Google Chrome instead (recommended, matches
what this script uses by default via BROWSER_CHANNEL = "chrome"):
  playwright install-deps          # only needed once, installs OS-level deps
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import time
import os
from datetime import datetime

# ============================================
# EDIT THESE SETTINGS
# ============================================

# "chrome" drives your real installed Google Chrome (needs Chrome on PATH,
# playwright finds it automatically once you've run `playwright install-deps`).
# Set to None to use Playwright's own bundled Chromium instead.
BROWSER_CHANNEL = "chrome"

# Folder where the browser profile (and your WhatsApp Web login) is kept.
# Unlike the old Selenium version, this makes the login PERSIST between runs
# -- scan the QR code once, and future runs skip straight past it.
USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".whatsapp_automator_profile")

# Run with a visible browser window (needed the first time, to scan the QR code)
HEADLESS = False

# How long to wait between messages (in seconds)
DELAY_BETWEEN_MESSAGES = 15

# CSS selectors WhatsApp Web uses for its message compose box, tried in order.
# WhatsApp changes these periodically. If sending starts failing with "Couldn't
# find the message box", open the browser (it's visible since HEADLESS=False),
# right-click the message box -> Inspect, and add the new selector to the front
# of this list.
MESSAGE_BOX_SELECTORS = [
    'div[contenteditable="true"][data-tab="10"]',
    'div[aria-placeholder="Type a message"]',
    'div[title="Type a message"]',
    'footer div[contenteditable="true"]',
    'div[contenteditable="true"][role="textbox"]',
]

# Your contacts (from the "تامر" sheet). Most are phone numbers with country
# code; a few are WhatsApp @usernames (no phone number available) -- both work
# with the wa.me link format used below.
CONTACTS = [
    "+201027561652",
    "+201222582650",
    "+201153279134",
    "+249902288788",
    "+201156783081",
    "+201116872327",
    "+972592729543",
    "+201552866834",
    "+201096141207",
    "+201276721393",
    "@mandooood",
    "+201096192295",
    "+201145187674",
    "+971521477122",
    "+966562537752",
    "+201149767798",
    "+201203893117",
    "+966597667077",
    "+201011644941",
    "+218934536455",
    "+201015453456",
    "+201551432466",
    "+201020742864",
    "+201120410022",
    "+201142800788",
    "+923136996392",
    "+201023014484",
    "+584268415091",
    "+201068464188",
    "+201105831650",
    "@MrAhmedMansour1793",
    "+201127565075",
    "+201036156620",
    "@Ahmed.Abd.ELfatttah",
    "+971561595646",
    "@Papajohns_marina.4",
    "+201558091111",
    "+201117804450",
    "+201004785469",
    "+201500047787",
    "+201206826783",
    "+201110343035",
    "+201018558418",
    "+201156662691",
    "+201129392465",
    "+972569101707",
    "+966564837012",
    "+201066456621",
    "+201158695533",
    "@youssefalmotassem",
    "@youssef_alsaudi0",
    "+962781608060",
]

# Your message
message_text = """
السلام عليكم ورحمة الله

*أهلاً وسهلاً بك من جديد في ضبط مصنع 🌹*


معك أخوك فى الله ( تامر السعيد )
 من قسم المتابعة الخاص بالدورة مجموعة *٣٤* 😍

باذن الله سأكون بصحبتك على مدار رحلتنا الطيبة للرد على كل الإستفسارات و إزالة كل العقبات قدر المستطاع لحصاد الثمار الطيبة من هذه الدورة الطيبة🌾
📌وماتنساش تطمني بنتيجة الإختبارات أولاً بأول 😊

زادكم الله فى الخير أعوام ونفع الله بكم البلاد و العباد 🤲
------------------------------
محتاجين نكون من الاوائل وده نعمله ان شاء الله عن طريق سماع المحاضرة كل جمعه الساعه 9 على اليوتيوب
 والامتحان بينزل الفجر نصلي الفجر ونمتحن وبكدا ان شاء الله نكون من الاوائل 😉🤍
هيا يا حبيب تالله لنزحفن سويا الي الجنة ❤️❤️
------------------------------
متنساش تقولي على اسم حضرتك عشان اسجله ❤️
تالله يا حبيب لنزحفن سويا الي الجنة.
"""

# ============================================
# DON'T EDIT BELOW THIS LINE
# ============================================

LOG_FILE = f"whatsapp_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"


def write_log(message):
    """Write a message to both console and log file"""
    print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def open_whatsapp(playwright):
    """Launch Chrome with a persistent profile and open WhatsApp Web"""
    write_log("Opening WhatsApp Web...")

    launch_kwargs = {"headless": HEADLESS}
    if BROWSER_CHANNEL:
        launch_kwargs["channel"] = BROWSER_CHANNEL
        write_log(f"Using browser channel: {BROWSER_CHANNEL}")
    else:
        write_log("Using Playwright's bundled Chromium")

    context = playwright.chromium.launch_persistent_context(USER_DATA_DIR, **launch_kwargs)
    page = context.new_page()
    page.goto("https://web.whatsapp.com")

    # WhatsApp's DOM changes too often to reliably auto-detect "logged in" by
    # CSS selector (that's what just timed out), so this asks you to confirm
    # once instead. With the persistent profile above, you should only need
    # to do this on the very first run -- after that WhatsApp Web should load
    # already logged in.
    write_log("\nIf a QR code appears, scan it with your phone.")
    input("Once your chats have loaded, press Enter here to continue... ")
    write_log("✓ Continuing")

    return context, page


def get_message_box(page):
    """Locate the message input box, trying each selector in
    MESSAGE_BOX_SELECTORS in turn (see the comment above that list)."""
    for selector in MESSAGE_BOX_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=8000)
            return page.locator(selector).last
        except PWTimeoutError:
            continue
    raise RuntimeError(
        "Couldn't find the message box with any known selector. Right-click "
        "the message box in the open browser -> Inspect, copy its selector, "
        "and add it to MESSAGE_BOX_SELECTORS at the top of this script."
    )


def send_message(page, contact, text=message_text):
    """Send a message to one contact (phone number or @username)"""
    try:
        if contact.startswith("@"):
            # web.whatsapp.com/send has no username parameter -- only wa.me
            # can open a chat by username. No text goes through this URL
            # though, so there's nothing here for a redirect to mangle.
            url = f"https://wa.me/{contact}"
        else:
            # Phone numbers open fully through web.whatsapp.com, same as
            # the original Selenium script.
            url = f"https://web.whatsapp.com/send?phone={contact}"
        write_log(url)
        page.goto(url)

        # Wait for the message box instead of a blind sleep
        message_box = get_message_box(page)
        time.sleep(2)

        # Type the message directly instead of pre-filling it via a URL
        # parameter -- that's what was mangling the emoji.
        message_box.click()
        page.keyboard.insert_text(text)
        time.sleep(1)
        message_box.press("Enter")
        write_log(f"✓ Sent to {contact}")
        return True
    except Exception as e:
        write_log(f"✗ Failed to send to {contact}: {e}")
        return False


def main():
    """Main function - runs everything"""
    write_log("=" * 50)
    write_log("WhatsApp Bulk Sender (Playwright) - Starting")
    write_log("=" * 50)
    write_log(f"Total contacts: {len(CONTACTS)}")
    write_log(f"Delay between messages: {DELAY_BETWEEN_MESSAGES} seconds")
    write_log(f"Log file: {LOG_FILE}")
    write_log("=" * 50)

    response = input("\nStart sending? (y/n): ").lower()
    if response != 'y':
        write_log("❌ CANCELLED by user")
        return

    write_log("✓ User confirmed - Starting process...")
    start_time = datetime.now()
    write_log(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    with sync_playwright() as playwright:
        context, page = open_whatsapp(playwright)

        success_count = 0
        fail_count = 0
        failed_contacts = []

        for i, contact in enumerate(CONTACTS, 1):
            write_log(f"\n[{i}/{len(CONTACTS)}] Processing: {contact}")
            if send_message(page, contact):
                success_count += 1
            else:
                fail_count += 1
                failed_contacts.append(contact)

            if i < len(CONTACTS):
                write_log(f"⏸️ Waiting {DELAY_BETWEEN_MESSAGES} seconds...")
                time.sleep(DELAY_BETWEEN_MESSAGES)

        end_time = datetime.now()
        duration = end_time - start_time

        write_log("\n" + "=" * 50)
        write_log("FINAL REPORT")
        write_log("=" * 50)
        write_log(f"✓ Successful: {success_count}")
        write_log(f"✗ Failed: {fail_count}")
        write_log(f"📊 Success Rate: {(success_count / len(CONTACTS) * 100):.1f}%")
        write_log(f"⏱️ Duration: {duration}")
        write_log(f"🕐 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if failed_contacts:
            write_log("\n❌ Failed Contacts List:")
            for contact in failed_contacts:
                write_log(f"  • {contact}")

        write_log("=" * 50)
        write_log(f"📄 Full log saved to: {LOG_FILE}")
        write_log("=" * 50)

        write_log("\nClosing browser in 10 seconds...")
        time.sleep(10)
        context.close()
        write_log("✓ Browser closed - Process complete!")


if __name__ == "__main__":
    main()