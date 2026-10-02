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
import random
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

# Delay between messages, in seconds. Randomized within this range each time
# instead of a fixed number -- sending at a perfectly identical interval is
# itself a pattern anti-spam systems look for.
DELAY_RANGE = (25, 55)

# Every this many messages, take one longer break, like a person would.
LONG_BREAK_EVERY = 10
LONG_BREAK_RANGE = (120, 240)  # seconds

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
message = """
السلام عليكم ورحمه الله وبركاته 

صباح الخير والقوة يا أبطال **المجموعة 34**! 🌟
اليوم هو **اليوم الثالث من الأسبوع الأول** في رحلتنا لـ **"ضبط المصنع"**، 
*والبداية القوية هي التي تصنع الفرق دائماً! 💪*

🔥 **مهمتنا اليوم:**
1. **سماع المحاضرة الأولى:** *"مفاهيم في مواجهة الحياة"* (استعدوا بتركيز).
*رابط المحاضرة*
https://youtu.be/IkvN1Idcqxs
2. **دخول الاختبار البسيط** الخاص بالمحاضرة لتثبيت المفاهيم.
*رابط الاختبار*
https://forms.gle/yakkWjrAbtj6H6Me9
3. **تأكيد اختيار مجموعتنا :** لا تنسوا اختيار **المجموعة 34** عند الاختبار 🎯
`كل خطوة صغيرة بتعملها اليوم هي جزء من التغيير الكبير اللي بتسعى له. بالتوفيق للجميع، ويلا بينا نصنع يوم مميز! 🚀✨`
"""

# ============================================
# DON'T EDIT BELOW THIS LINE
# ============================================

LOG_FILE = f"whatsapp_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"


def write_log(entry):
    """Write a message to both console and log file"""
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {entry}\n")


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


def type_message(page):
    """Type the `message` variable into the focused compose box. The clipboard
    is never used. Line breaks are entered as Shift+Enter so they stay inside
    the message instead of sending it."""
    lines = message.split("\n")
    for i, line in enumerate(lines):
        if line:
            page.keyboard.insert_text(line)
        if i < len(lines) - 1:
            page.keyboard.press("Shift+Enter")


def send_message(page, contact):
    """Send the `message` variable to one contact (phone number or @username)"""
    try:
        if contact.startswith("@"):
            username = contact[1:]  # strip the leading @
            # web.whatsapp.com/send supports opening a chat by username too,
            # via type=username -- no text passed through this URL, so
            # there's nothing here for a redirect to mangle either way.
            url = f"https://web.whatsapp.com/send/?username={username}&type=username"
        else:
            # Phone numbers open fully through web.whatsapp.com, same as
            # the original Selenium script.
            url = f"https://web.whatsapp.com/send?phone={contact}"
        write_log(url)
        page.goto(url)

        # Wait for the message box instead of a blind sleep
        message_box = get_message_box(page)

        # Pause as if reading the chat before starting to type
        time.sleep(random.uniform(1.5, 4.0))

        message_box.click()
        type_message(page)

        # Pause as if reviewing the message before sending
        time.sleep(random.uniform(0.8, 2.5))
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
    write_log(f"Delay between messages: {DELAY_RANGE[0]}-{DELAY_RANGE[1]}s (randomized)")
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
                if i % LONG_BREAK_EVERY == 0:
                    pause = random.uniform(*LONG_BREAK_RANGE)
                    write_log(f"⏸️ Taking a longer break: {pause:.0f}s...")
                else:
                    pause = random.uniform(*DELAY_RANGE)
                    write_log(f"⏸️ Waiting {pause:.0f}s...")
                time.sleep(pause)

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
