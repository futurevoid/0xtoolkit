"""
0xWhatsautomator - Playwright edition

Sends `message` (below) to every contact in CONTACTS through WhatsApp Web,
fully automatically and in the background (no browser window, no prompts).

Install once:
  pip install playwright
  playwright install chromium     # fallback browser if Google Chrome isn't installed

Run:
  python 0xWhatsautomator.py

First run only: a browser window opens with the WhatsApp QR code. Scan it with
your phone (WhatsApp -> Linked devices -> Link a device); the window closes
itself and everything else runs in the background. Later runs need nothing.

Every contact that got the message is saved to whatsapp_sent_contacts.txt and
skipped next time, so if a run is interrupted, just run it again. Delete that
file to send a NEW message to everyone.
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

# True = send fully in the background with no browser window.
# If you're not logged in yet, a visible window opens ONLY to show the QR
# code: scan it with your phone (WhatsApp -> Linked devices -> Link a device),
# the window closes by itself and sending continues in the background. The
# login is kept in USER_DATA_DIR, so later runs need no window at all.
# False = keep the browser window visible the whole time (it still works
# while minimized or behind other windows -- never click on it).
HEADLESS = True

# Max time to wait for WhatsApp Web to load / for the QR code to be scanned.
LOGIN_TIMEOUT = 300  # seconds

# True = ask "Start sending? (y/n)" before starting. False = fully automatic.
CONFIRM_BEFORE_SENDING = False

# Delay between messages, in seconds. Randomized within this range each time
# instead of a fixed number -- sending at a perfectly identical interval is
# itself a pattern anti-spam systems look for.
DELAY_RANGE = (25, 55)

# Every this many messages, take one longer break, like a person would.
LONG_BREAK_EVERY = 10
LONG_BREAK_RANGE = (120, 240)  # seconds

# How long to wait for a chat to open after loading its link, in seconds.
CHAT_LOAD_TIMEOUT = 40

# Seconds to wait after typing before sending when the message contains a
# link, so WhatsApp finishes building the link preview.
LINK_PREVIEW_WAIT = 4

# True = type the message into each chat but DON'T send it (for testing).
DRY_RUN = False

# Contacts that got the message are written to this file. On the next run
# they are skipped, so a crash or Ctrl+C never makes anyone get it twice.
# Delete the file (or set SKIP_ALREADY_SENT = False) to send to everyone again.
SENT_FILE = "whatsapp_sent_contacts.txt"
SKIP_ALREADY_SENT = True

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

# Words in the popup WhatsApp Web shows when the number in the /send URL has
# no WhatsApp account (English and Arabic interface)
INVALID_NUMBER_TEXTS = ["invalid", "غير صالح", "غير صحيح"]

# Something on screen that only exists once you're logged in (chat list etc.)
LOGGED_IN_SELECTORS = [
    '#pane-side',
    '#side',
    'div[aria-label="Chat list"]',
    'div[aria-label="قائمة الدردشات"]',
    '[data-icon="new-chat-outline"]',
]

# The login QR code
QR_SELECTORS = [
    'canvas[aria-label*="QR"]',
    'canvas[aria-label*="scan" i]',
    'div[data-ref] canvas',
]

# Keep Chrome running at full speed when it's headless, minimized or covered
BROWSER_ARGS = [
    "--disable-backgrounding-occluded-windows",
    "--disable-renderer-backgrounding",
    "--disable-background-timer-throttling",
    "--disable-blink-features=AutomationControlled",
]


class NotLoggedInError(Exception):
    pass


# Send button, used only if pressing Enter didn't send the message
SEND_BUTTON_SELECTORS = [
    'button[aria-label="Send"]',
    'span[data-icon="send"]',
    'span[data-icon="wds-ic-send-filled"]',
]


def write_log(entry):
    """Write a message to both console and log file"""
    print(entry)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {entry}\n")


def normalize(text):
    """Collapse a message to its visible lines, so what's in the compose box
    can be compared with `message` regardless of how the editor stores
    line breaks and spaces."""
    text = text.replace(" ", " ").replace("\r", "")
    return "\n".join(line.strip() for line in text.strip().split("\n"))


def load_sent_contacts():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, encoding='utf-8') as f:
        return {line.strip() for line in f if line.strip()}


def mark_sent(contact):
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(contact + "\n")


def any_visible(page, selectors):
    for selector in selectors:
        try:
            loc = page.locator(selector).first
            if loc.count() and loc.is_visible():
                return True
        except Exception:
            pass
    return False


def launch_browser(playwright, headless):
    """Start Chrome (or the bundled Chromium as a fallback) on the saved
    profile and return (context, page)."""
    channels = [BROWSER_CHANNEL] if BROWSER_CHANNEL else []
    if "chromium" not in channels:
        channels.append("chromium")

    kwargs = {"headless": headless, "args": BROWSER_ARGS}
    if headless:
        kwargs["viewport"] = {"width": 1366, "height": 900}
    else:
        kwargs["no_viewport"] = True

    last_error = None
    for channel in channels:
        try:
            context = playwright.chromium.launch_persistent_context(
                USER_DATA_DIR, channel=channel, **kwargs)
        except Exception as e:
            last_error = e
            write_log(f"Couldn't start browser '{channel}', trying the next one "
                      f"({str(e).splitlines()[0]})")
            continue

        page = context.pages[0] if context.pages else context.new_page()
        if headless:
            # Headless Chrome calls itself "HeadlessChrome", which WhatsApp
            # Web rejects. Restart it presenting the normal Chrome name.
            user_agent = page.evaluate("navigator.userAgent")
            if "HeadlessChrome" in user_agent:
                context.close()
                context = playwright.chromium.launch_persistent_context(
                    USER_DATA_DIR, channel=channel,
                    user_agent=user_agent.replace("HeadlessChrome", "Chrome"), **kwargs)
                page = context.pages[0] if context.pages else context.new_page()

        # Accept any "leave site? changes may not be saved" prompt, otherwise
        # it silently blocks the navigation to the next contact.
        page.on("dialog", lambda dialog: dialog.accept())
        write_log(f"Browser: {channel} ({'background' if headless else 'visible window'})")
        return context, page
    raise RuntimeError(f"Couldn't start any browser: {last_error}")


def check_login(page, wait_for_scan):
    """Load WhatsApp Web and return True once logged in. If the QR code is
    showing: return False right away, or (wait_for_scan=True) wait for it to
    be scanned."""
    page.goto("https://web.whatsapp.com")
    deadline = time.time() + LOGIN_TIMEOUT
    asked = False
    no_qr_since = time.time()
    while time.time() < deadline:
        if any_visible(page, LOGGED_IN_SELECTORS):
            return True
        if any_visible(page, QR_SELECTORS):
            no_qr_since = time.time()
            if not wait_for_scan:
                return False
            if not asked:
                write_log("\n📱 Scan the QR code in the browser window with your phone:")
                write_log("   WhatsApp -> Settings -> Linked devices -> Link a device")
                asked = True
        elif time.time() - no_qr_since > 45:
            # WhatsApp has been loading for 45s without asking for a QR scan,
            # so the session is logged in even though none of the known
            # chat-list selectors matched (WhatsApp renames them sometimes).
            return True
        time.sleep(1)
    return False


def open_whatsapp(playwright):
    """Open WhatsApp Web logged in. Shows a window only if a QR scan is
    needed, then continues in the background (when HEADLESS = True)."""
    write_log("Opening WhatsApp Web...")
    context, page = launch_browser(playwright, HEADLESS)
    if check_login(page, wait_for_scan=not HEADLESS):
        write_log("✓ Logged in")
        return context, page

    if not HEADLESS:
        context.close()
        raise NotLoggedInError(f"QR code wasn't scanned within {LOGIN_TIMEOUT}s")

    # Not logged in: show a window just for the QR code.
    context.close()
    write_log("Not logged in yet -- opening a window to scan the QR code...")
    context, page = launch_browser(playwright, headless=False)
    if not check_login(page, wait_for_scan=True):
        context.close()
        raise NotLoggedInError(f"QR code wasn't scanned within {LOGIN_TIMEOUT}s")
    write_log("✓ Logged in -- letting WhatsApp finish syncing...")
    time.sleep(15)
    context.close()

    write_log("Continuing in the background...")
    context, page = launch_browser(playwright, headless=True)
    if not check_login(page, wait_for_scan=False):
        context.close()
        raise NotLoggedInError("login didn't stick after scanning, run the script again")
    write_log("✓ Logged in")
    return context, page


def get_message_box(page):
    """Wait for the chat to open and return its compose box. Raises if the
    number isn't on WhatsApp or the box can't be found."""
    deadline = time.time() + CHAT_LOAD_TIMEOUT
    while time.time() < deadline:
        for selector in MESSAGE_BOX_SELECTORS:
            box = page.locator(selector).last
            try:
                if box.count() and box.is_visible():
                    return box
            except Exception:
                pass
        if any_visible(page, QR_SELECTORS):
            raise NotLoggedInError("WhatsApp logged out (QR code is showing)")
        try:
            popup = page.locator('div[role="dialog"]')
            popup_text = popup.first.inner_text().lower() if popup.count() else ""
            if any(word in popup_text for word in INVALID_NUMBER_TEXTS):
                raise RuntimeError("number is not on WhatsApp (invalid number popup)")
        except PWTimeoutError:
            pass
        time.sleep(0.5)
    raise RuntimeError(
        f"chat didn't open within {CHAT_LOAD_TIMEOUT}s. If WhatsApp is loaded "
        "but this keeps happening, right-click the message box -> Inspect, "
        "and add its selector to the front of MESSAGE_BOX_SELECTORS."
    )


def clear_box(page, box):
    box.click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")


def box_text(box):
    return normalize(box.inner_text())


def type_message(page, box):
    """Type the `message` variable into the compose box (never the clipboard).
    Line breaks are entered with Shift+Enter so they don't send early."""
    box.click()
    lines = normalize(message).split("\n")
    for i, line in enumerate(lines):
        if line:
            page.keyboard.insert_text(line)
            time.sleep(random.uniform(0.05, 0.25))
        if i < len(lines) - 1:
            page.keyboard.press("Shift+Enter")


def send_message(page, contact):
    """Send the `message` variable to one contact (phone number or @username).
    Returns True only once the message has actually left the compose box."""
    try:
        if contact.startswith("@"):
            url = f"https://web.whatsapp.com/send/?username={contact[1:]}&type=username"
        else:
            url = f"https://web.whatsapp.com/send?phone={contact.lstrip('+')}"
        write_log(url)
        page.goto(url)

        box = get_message_box(page)

        # Pause as if reading the chat before starting to type
        time.sleep(random.uniform(1.5, 4.0))

        # Make sure the box holds exactly `message` -- clear any leftover
        # draft first, and retype if anything came out wrong.
        expected = normalize(message)
        for attempt in range(1, 4):
            if box_text(box):
                clear_box(page, box)
            type_message(page, box)
            if box_text(box) == expected:
                break
            write_log(f"  typed text didn't match the message (attempt {attempt}), retyping")
        else:
            clear_box(page, box)
            raise RuntimeError("couldn't type the message correctly, NOT sent")

        # Links in the message make WhatsApp load a preview; give it time so
        # Enter isn't swallowed while it loads.
        if "http" in message:
            time.sleep(LINK_PREVIEW_WAIT)

        # Pause as if reviewing the message before sending
        time.sleep(random.uniform(0.8, 2.5))

        if DRY_RUN:
            write_log(f"✓ [DRY RUN] Message typed for {contact}, not sent")
            clear_box(page, box)
            return True

        box.press("Enter")
        if not wait_until_sent(box):
            for selector in SEND_BUTTON_SELECTORS:
                button = page.locator(selector).last
                if button.count() and button.is_visible():
                    button.click()
                    break
            if not wait_until_sent(box):
                raise RuntimeError("message is still in the box after Enter and Send button")

        # Let WhatsApp hand the message off before navigating away
        time.sleep(2)
        write_log(f"✓ Sent to {contact}")
        return True
    except NotLoggedInError:
        raise
    except Exception as e:
        write_log(f"✗ Failed to send to {contact}: {e}")
        return False


def wait_until_sent(box, timeout=10):
    """A sent message leaves the compose box empty."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if not box_text(box):
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def main():
    """Main function - runs everything"""
    already_sent = load_sent_contacts() if SKIP_ALREADY_SENT else set()
    pending = [c for c in CONTACTS if c not in already_sent]

    write_log("=" * 50)
    write_log("WhatsApp Bulk Sender (Playwright) - Starting")
    write_log("=" * 50)
    write_log(f"Total contacts: {len(CONTACTS)}")
    if already_sent:
        write_log(f"Skipping {len(CONTACTS) - len(pending)} already sent (listed in {SENT_FILE})")
    write_log(f"To send now: {len(pending)}")
    if DRY_RUN:
        write_log("DRY RUN: messages will be typed but NOT sent")
    write_log(f"Delay between messages: {DELAY_RANGE[0]}-{DELAY_RANGE[1]}s (randomized)")
    write_log(f"Log file: {LOG_FILE}")
    write_log("=" * 50)
    write_log("Message preview:\n" + normalize(message))
    write_log("=" * 50)

    if not pending:
        write_log(f"Nothing to send. Delete {SENT_FILE} to send to everyone again.")
        return

    if CONFIRM_BEFORE_SENDING:
        response = input("\nStart sending? (y/n): ").strip().lower()
        if response != 'y':
            write_log("❌ CANCELLED by user")
            return

    start_time = datetime.now()
    write_log(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    with sync_playwright() as playwright:
        try:
            context, page = open_whatsapp(playwright)
        except NotLoggedInError as e:
            write_log(f"❌ Not logged in: {e}. Nothing was sent.")
            return

        success_count = 0
        failed_contacts = []

        try:
            for i, contact in enumerate(pending, 1):
                write_log(f"\n[{i}/{len(pending)}] Processing: {contact}")
                if send_message(page, contact):
                    success_count += 1
                    if not DRY_RUN:
                        mark_sent(contact)
                else:
                    failed_contacts.append(contact)

                if i < len(pending):
                    if i % LONG_BREAK_EVERY == 0:
                        pause = random.uniform(*LONG_BREAK_RANGE)
                        write_log(f"⏸️ Taking a longer break: {pause:.0f}s...")
                    else:
                        pause = random.uniform(*DELAY_RANGE)
                        write_log(f"⏸️ Waiting {pause:.0f}s...")
                    time.sleep(pause)
        except KeyboardInterrupt:
            write_log("\n⛔ Stopped by user (Ctrl+C). Re-run to continue where it left off.")
        except NotLoggedInError as e:
            write_log(f"\n⛔ Stopped: {e}. Run the script again to log in and continue "
                      "where it left off.")

        end_time = datetime.now()
        attempted = success_count + len(failed_contacts)

        write_log("\n" + "=" * 50)
        write_log("FINAL REPORT")
        write_log("=" * 50)
        write_log(f"✓ Successful: {success_count}")
        write_log(f"✗ Failed: {len(failed_contacts)}")
        if attempted:
            write_log(f"📊 Success Rate: {(success_count / attempted * 100):.1f}%")
        write_log(f"⏱️ Duration: {end_time - start_time}")
        write_log(f"🕐 End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if failed_contacts:
            write_log("\n❌ Failed Contacts List:")
            for contact in failed_contacts:
                write_log(f"  • {contact}")

        write_log("=" * 50)
        write_log(f"📄 Full log saved to: {LOG_FILE}")
        write_log("=" * 50)

        write_log("\nClosing browser...")
        time.sleep(5)
        context.close()
        write_log("✓ Browser closed - Process complete!")


if __name__ == "__main__":
    main()
