"""
0xWhatsautomator - Playwright edition

Sends `message` (below) to every contact in CONTACTS through WhatsApp Web,
fully automatically: no prompts, and the browser window minimizes itself and
keeps sending while minimized or behind other windows.

Install once:
  pip install playwright
  playwright install chromium     # fallback browser if Google Chrome isn't installed

Run:
  python 0xWhatsautomator.py

First run only: scan the QR code shown in the browser window with your phone
(WhatsApp -> Linked devices -> Link a device). The login is saved, so later
runs need nothing from you.

Check what was sent: whatsapp_sent_proof/ has, per contact, the exact text
typed before sending and the text of the sent chat bubble.

No double sends: a contact is skipped if they already got this exact message
(recorded in whatsapp_sent_contacts.txt, and checked in the chat itself before
typing). If a run is interrupted, just run it again. Change `message` and
everyone gets the new one -- nothing to delete.
"""

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import time
import os
import random
import re
import hashlib
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

# False = normal browser window (recommended). It works while minimized or
# behind other windows -- you never need to click on it or keep it in front.
# True = no window at all. If you're not logged in yet, a window opens ONLY to
# show the QR code, then sending continues with no window.
HEADLESS = False

# Minimize the window automatically once WhatsApp is logged in (the window
# stays open for the QR code if you need to scan it first). Sending works the
# same minimized; restore the window any time to watch it.
START_MINIMIZED = True

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

# Proof of exactly what was sent, saved per contact into this folder:
#   <contact>.txt          -- the text in the message box right before sending,
#                             and the text of the sent bubble in the chat after
#   <contact>_1_before_send.png / <contact>_2_sent.png -- screenshots, only
#                             when the window isn't minimized (a minimized
#                             window can't be captured)
# None = off.
PROOF_DIR = "whatsapp_sent_proof"

# Never send the same message to the same contact twice. Two checks:
#  1. Every contact that gets `message` is recorded in SENT_FILE together with
#     a fingerprint of the message; they're skipped on later runs. Change
#     `message` and everyone gets the new one -- nothing to delete.
#  2. Before typing, the chat itself is checked: if this exact message is
#     already among your sent messages there (sent by an earlier run, from
#     another computer, or by hand), the contact is skipped.
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
    "+201096141207",
    "+201027561652",
    "+201222582650",
    "+201153279134",
    "+249902288788",
    "+201156783081",
    "+201116872327",
    "+972592729543",
    "+201552866834",
    
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

# Words in the popup WhatsApp Web shows when the number in the /send URL has
# no WhatsApp account (English and Arabic interface)
INVALID_NUMBER_TEXTS = ["invalid", "غير صالح", "غير صحيح"]

# Reads the messages of the open chat (oldest first) as [{text, out}], where
# out = sent by you. Finds messages by what WhatsApp needs for its own copy and
# reply features rather than by class names, which it renames:
#   [data-pre-plain-text]  -- on every text message ("[time, date] Name: ")
#   [data-id]              -- on every message row, starting "true_" if yours
# with the old div.message-out / div.message-in classes as a fallback.
CHAT_MESSAGES_JS = """(limit) => {
    const read = el => {
        const copy = el.cloneNode(true);
        copy.querySelectorAll('img').forEach(img =>
            img.replaceWith(document.createTextNode(img.alt || img.getAttribute('data-plain-text') || '')));
        copy.querySelectorAll('br').forEach(br => br.replaceWith(document.createTextNode('\\n')));
        copy.querySelectorAll('p, div, li').forEach(b => b.append(document.createTextNode('\\n')));
        return copy.textContent;
    };
    const root = document.querySelector('#main') || document.body;
    let nodes = [];
    for (const sel of ['[data-pre-plain-text]', '.message-out, .message-in',
                       '[data-id^="true_"], [data-id^="false_"]']) {
        nodes = [...root.querySelectorAll(sel)];
        if (nodes.length) break;
    }
    nodes = nodes.filter(n => !nodes.some(o => o !== n && o.contains(n)));   // whole messages only
    return nodes.slice(-limit).map(n => {
        const row = n.closest('[data-id]');
        const id = row ? row.getAttribute('data-id') || '' : '';
        const out = id.startsWith('true_') || !!n.closest('.message-out');
        return {text: read(n), out: out};
    });
}"""

# Anything that shows the open chat has message history on screen
HISTORY_PRESENT_JS = """() => {
    const root = document.querySelector('#main');
    const inRoot = root ? root.querySelectorAll('[data-pre-plain-text], [data-id], [role="row"]').length : 0;
    return inRoot + document.querySelectorAll(
        '[data-pre-plain-text], .message-out, .message-in, [data-id^="true_"], [data-id^="false_"]').length;
}"""

# How many of your latest sent messages in the chat are checked, and how long
# to wait for the chat history to appear before checking.
HISTORY_MESSAGES_TO_CHECK = 50
HISTORY_LOAD_WAIT = 8  # seconds

# WhatsApp only shows the newest few messages of a chat; the script scrolls up
# until it has at least this many to check (or reaches the start of the chat).
MIN_MESSAGES_TO_CHECK = 10

# Scrolls the open chat's message list (the tallest scrollable box in #main)
# up by one screen. Returns "moved", "top" (already at the top -- WhatsApp is
# nudged to load older messages) or "none" (no scrollable list found).
SCROLL_CHAT_UP_JS = """() => {
    const root = document.querySelector('#main') || document.body;
    let best = null;
    for (const el of root.querySelectorAll('div')) {
        const style = getComputedStyle(el);
        if (/(auto|scroll)/.test(style.overflowY) && el.scrollHeight > el.clientHeight + 10 &&
            (!best || el.scrollHeight > best.scrollHeight)) best = el;
    }
    if (!best) return 'none';
    if (best.scrollTop <= 0) {
        best.dispatchEvent(new Event('scroll'));
        return 'top';
    }
    best.scrollTop = Math.max(0, best.scrollTop - best.clientHeight);
    best.dispatchEvent(new Event('scroll'));
    return 'moved';
}"""

# The "Read more" link on long messages (English and Arabic interface)
READ_MORE_WORDS = r"(read more|قراءة المزيد|اقرأ المزيد|عرض المزيد|المزيد)"
READ_MORE_PATTERN = re.compile(READ_MORE_WORDS + r"\s*$", re.I)
READ_MORE_LINK = re.compile(r"^\s*" + READ_MORE_WORDS + r"\s*$", re.I)

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
    "--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling",
    "--disable-blink-features=AutomationControlled",
]

# Runs in WhatsApp's page before its own code: the page always sees itself as
# visible and focused, so a minimized/covered window behaves exactly like one
# in front (WhatsApp pauses some work in hidden tabs).
ALWAYS_VISIBLE_JS = """
Object.defineProperty(Document.prototype, 'visibilityState', {get: () => 'visible'});
Object.defineProperty(Document.prototype, 'hidden', {get: () => false});
Object.defineProperty(Document.prototype, 'webkitVisibilityState', {get: () => 'visible'});
Object.defineProperty(Document.prototype, 'webkitHidden', {get: () => false});
Document.prototype.hasFocus = () => true;
for (const type of ['visibilitychange', 'webkitvisibilitychange', 'blur', 'pagehide', 'freeze']) {
  window.addEventListener(type, e => { if (e.target === window || e.target === document) e.stopImmediatePropagation(); }, true);
  document.addEventListener(type, e => e.stopImmediatePropagation(), true);
}
"""


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


# Reads text the way WhatsApp displays it: WhatsApp draws emoji as <img>
# pictures (the emoji itself is in their alt text) and puts every line in its
# own paragraph, so plain innerText would drop the emoji and add blank lines.
READ_TEXT_JS = """el => {
    const copy = el.cloneNode(true);
    copy.querySelectorAll('img').forEach(img =>
        img.replaceWith(document.createTextNode(img.alt || img.getAttribute('data-plain-text') || '')));
    copy.querySelectorAll('br').forEach(br => br.replaceWith(document.createTextNode('\\n')));
    copy.querySelectorAll('p, div, li').forEach(block => block.append(document.createTextNode('\\n')));
    return copy.textContent;
}"""

# Invisible characters WhatsApp may add or drop (direction marks, emoji
# variation selectors, zero-width joiners/spaces) -- ignored when comparing.
INVISIBLE_CHARS = set("\u200b\u200c\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e"
                      "\u2066\u2067\u2068\u2069\ufe0e\ufe0f\ufeff")


def read_text(locator):
    """Text of an element as displayed (emoji included), see READ_TEXT_JS."""
    text = locator.evaluate(READ_TEXT_JS)
    text = "".join(ch for ch in text if ch not in INVISIBLE_CHARS)
    return "\n".join(line for line in normalize(text).split("\n") if line) if text.strip() else ""


def first_difference(expected, actual):
    """Short description of where two texts first differ (for the log)."""
    a, b = plain(expected), plain(actual)
    i = next((n for n in range(min(len(a), len(b))) if a[n] != b[n]), min(len(a), len(b)))
    return (f"first difference at character {i}: expected ...{a[max(0, i - 15):i + 15]}... "
            f"but the box has ...{b[max(0, i - 15):i + 15]}...")


def normalize(text):
    """Collapse a message to its visible lines, so what's in the compose box
    can be compared with `message` regardless of how the editor stores
    line breaks and spaces."""
    text = text.replace(" ", " ").replace("\r", "")
    return "\n".join(line.strip() for line in text.strip().split("\n"))


def proof_path(contact, suffix):
    os.makedirs(PROOF_DIR, exist_ok=True)
    name = "".join(ch if ch.isalnum() else "_" for ch in contact.lstrip("+@"))
    return os.path.join(PROOF_DIR, name + suffix)


def is_minimized(page):
    try:
        cdp = page.context.new_cdp_session(page)
        window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
        state = cdp.send("Browser.getWindowBounds", {"windowId": window_id})["bounds"]["windowState"]
        cdp.detach()
        return state == "minimized"
    except Exception:
        return False


def save_proof(page, contact, step, text):
    """Record what was typed / sent (see PROOF_DIR); never fails the send."""
    if not PROOF_DIR:
        return
    try:
        with open(proof_path(contact, ".txt"), "a", encoding="utf-8") as f:
            f.write(f"===== {step} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) =====\n")
            f.write(text + "\n\n")
        if not is_minimized(page):
            page.screenshot(path=proof_path(contact, f"_{step}.png"), timeout=5000)
    except Exception as e:
        write_log(f"  (couldn't save proof: {str(e).splitlines()[0]})")


def last_sent_bubble_text(page):
    """Text of the newest message you sent in the open chat, or None."""
    expand_read_more(page)
    messages = chat_messages(page)
    mine = [m["text"] for m in messages if m["out"]]
    if mine:
        return mine[-1]
    # direction unknown: right after sending, the newest message is ours
    return messages[-1]["text"] if messages else None


def plain(text):
    """Text without WhatsApp formatting marks (*bold* _italic_ ~strike~ `code`)
    or whitespace -- for comparing with what the chat bubble displays."""
    return "".join(ch for ch in text
                   if ch not in "*_~`" and ch not in INVISIBLE_CHARS and not ch.isspace())


def contact_key(contact):
    """Same contact however it's written: "+20 10..." == "2010...", case-insensitive @usernames."""
    contact = contact.strip().lower()
    if contact.startswith("@"):
        return contact
    return "".join(ch for ch in contact if ch.isdigit())


def message_id():
    """Fingerprint of `message`, so the record knows WHICH message was sent."""
    return hashlib.sha256(plain(normalize(message)).encode("utf-8")).hexdigest()[:16]


def load_sent_contacts():
    """Contacts that already got THIS message, from SENT_FILE."""
    if not os.path.exists(SENT_FILE):
        return set()
    sent = set()
    with open(SENT_FILE, encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) >= 2 and parts[1] == message_id():
                sent.add(contact_key(parts[0]))
    return sent


def mark_sent(contact):
    with open(SENT_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{contact}\t{message_id()}\t{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def expand_read_more(page):
    """WhatsApp cuts long messages short behind "Read more"; open them all."""
    try:
        area = page.locator("#main") if page.locator("#main").count() else page
        links = area.get_by_text(READ_MORE_LINK)
        for i in range(min(links.count(), 20)):
            try:
                links.nth(i).click(timeout=2000)
            except Exception:
                pass
        if links.count():
            time.sleep(0.5)
    except Exception:
        pass


def chat_messages(page):
    """Latest messages of the open chat as [{"text", "out"}] (see CHAT_MESSAGES_JS)."""
    try:
        messages = page.evaluate(CHAT_MESSAGES_JS, HISTORY_MESSAGES_TO_CHECK)
    except Exception:
        return []
    for m in messages:
        text = "".join(ch for ch in m["text"] if ch not in INVISIBLE_CHARS)
        m["text"] = "\n".join(line for line in normalize(text).split("\n") if line)
    return [m for m in messages if m["text"]]


def history_present(page):
    try:
        return page.evaluate(HISTORY_PRESENT_JS) > 0
    except Exception:
        return False


DOM_DUMPS_LEFT = [3]


def dump_chat_dom(page, contact):
    """Save the open chat's page structure (a few per run) so the selectors can
    be fixed if WhatsApp changed its layout."""
    if not PROOF_DIR or DOM_DUMPS_LEFT[0] <= 0:
        return
    DOM_DUMPS_LEFT[0] -= 1
    try:
        html = page.evaluate("() => (document.querySelector('#main') || document.body).outerHTML")
        path = proof_path(contact, "_chat_page.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html[:400000])
        write_log(f"  saved the chat's page structure to {path}")
    except Exception:
        pass


def fingerprint(text):
    """Only the letters and numbers of a message, in order. WhatsApp displays
    list numbers ("1. "), emoji, formatting marks and spacing differently from
    how they're typed, but never changes the words -- so two messages with the
    same fingerprint are the same message, and a message with even one
    different word or link is a different one."""
    text = re.sub(r"(?m)^\s*(\d+[.)]|[-•])\s+", "", text)   # list markers
    text = READ_MORE_PATTERN.sub("", text)
    return "".join(ch for ch in text.lower() if ch.isalnum())


def same_message(bubble_text):
    """True if a chat bubble shows `message`. Also accepts a bubble WhatsApp
    cut short behind "Read more" when its visible part is a long, exact start
    of `message`."""
    wanted, shown = fingerprint(normalize(message)), fingerprint(bubble_text)
    if not shown:
        return False
    if wanted in shown:
        return True
    cut_short = bool(READ_MORE_PATTERN.search(bubble_text)) or bubble_text.rstrip().endswith("…")
    return (cut_short and wanted.startswith(shown)
            and len(shown) >= 150 and len(shown) >= 0.6 * len(wanted))


def wait_for_history(page):
    """Give the chat history time to appear (new chats have none)."""
    deadline = time.time() + HISTORY_LOAD_WAIT
    while time.time() < deadline:
        if history_present(page):
            time.sleep(1.5)  # let the rest of the visible history render
            return True
        time.sleep(0.5)
    return False


def load_older_messages(page):
    """Scroll the chat up until at least MIN_MESSAGES_TO_CHECK messages are
    loaded, or the start of the chat is reached."""
    count = len(chat_messages(page))
    fruitless = 0
    for _ in range(20):
        if count >= MIN_MESSAGES_TO_CHECK:
            return
        try:
            where = page.evaluate(SCROLL_CHAT_UP_JS)
        except Exception:
            where = "none"
        # WhatsApp loads older messages as you scroll; give it up to 3s
        deadline = time.time() + 3
        new_count = count
        while time.time() < deadline:
            time.sleep(0.5)
            new_count = len(chat_messages(page))
            if new_count > count:
                break
        if new_count > count:
            count, fruitless = new_count, 0
        elif where in ("top", "none"):
            return  # start of the chat (or nothing to scroll): all loaded
        else:
            fruitless += 1
            if fruitless >= 4:
                return


def already_in_chat(page, contact):
    """True if `message` is already among the latest messages in this chat."""
    wait_for_history(page)
    load_older_messages(page)
    expand_read_more(page)
    messages = chat_messages(page)
    # Any message in the chat counts (not only ones marked as yours), so a
    # missed "sent by you" marker can never cause a duplicate.
    if any(same_message(m["text"]) for m in messages):
        return True
    if messages:
        mine = sum(1 for m in messages if m["out"])
        write_log(f"  checked the last {len(messages)} message(s) in this chat "
                  f"({mine} sent by you): this message wasn't sent before")
        save_proof(page, contact, "chat_before_send",
                   "\n----------\n".join(m["text"] for m in messages[-MIN_MESSAGES_TO_CHECK:]))
        if len(messages) < MIN_MESSAGES_TO_CHECK or not mine:
            # fewer than expected, or none recognised as yours: keep the page
            # structure so the reading can be fixed for your WhatsApp version
            dump_chat_dom(page, contact)
    elif history_present(page):
        write_log("  ⚠ the chat has messages but they couldn't be read -- "
                  "relying on the sent record only")
        dump_chat_dom(page, contact)
    else:
        write_log("  no earlier messages found in this chat")
        dump_chat_dom(page, contact)
    return False


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

        context.add_init_script(ALWAYS_VISIBLE_JS)
        # Accept any "leave site? changes may not be saved" prompt, otherwise
        # it silently blocks the navigation to the next contact.
        page.on("dialog", lambda dialog: dialog.accept())
        write_log(f"Browser: {channel} ({'background' if headless else 'visible window'})")
        return context, page
    raise RuntimeError(f"Couldn't start any browser: {last_error}")


def minimize_window(page):
    """Minimize the browser window (sending keeps working while minimized)."""
    try:
        cdp = page.context.new_cdp_session(page)
        window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
        cdp.send("Browser.setWindowBounds",
                 {"windowId": window_id, "bounds": {"windowState": "minimized"}})
        write_log("Window minimized -- sending continues in the background")
    except Exception as e:
        write_log(f"(couldn't minimize the window: {e})")


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
    """Open WhatsApp Web logged in (waiting for a QR scan if needed)."""
    write_log("Opening WhatsApp Web...")
    context, page = launch_browser(playwright, HEADLESS)
    if check_login(page, wait_for_scan=not HEADLESS):
        write_log("✓ Logged in")
        if not HEADLESS and START_MINIMIZED:
            minimize_window(page)
        return context, page

    if not HEADLESS:
        context.close()
        raise NotLoggedInError(f"QR code wasn't scanned within {LOGIN_TIMEOUT}s")

    # Headless and not logged in: show a window just for the QR code.
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
    return read_text(box)


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


SENT, ALREADY_SENT, FAILED = "sent", "already sent", "failed"


def send_message(page, contact):
    """Send the `message` variable to one contact (phone number or @username).
    Returns SENT only once the message has actually left the compose box,
    ALREADY_SENT if the chat already has this exact message, else FAILED."""
    try:
        if contact.startswith("@"):
            url = f"https://web.whatsapp.com/send/?username={contact[1:]}&type=username"
        else:
            url = f"https://web.whatsapp.com/send?phone={contact.lstrip('+')}"
        write_log(url)
        page.goto(url)

        box = get_message_box(page)

        # Pause as if reading the chat before starting to type (this also
        # gives the chat history time to load for the check below)
        time.sleep(random.uniform(2.5, 4.5))

        if SKIP_ALREADY_SENT and already_in_chat(page, contact):
            write_log(f"↷ Skipped {contact}: this message is already in the chat")
            return ALREADY_SENT

        # Make sure the box holds exactly `message` -- clear any leftover
        # draft first, and retype if anything came out wrong.
        expected = normalize(message)
        # Compared ignoring line spacing, formatting marks and invisible
        # characters, which WhatsApp's editor changes on its own.
        for attempt in range(1, 4):
            if box_text(box):
                clear_box(page, box)
            type_message(page, box)
            typed = box_text(box)
            if plain(typed) == plain(expected):
                break
            write_log(f"  typed text didn't match the message (attempt {attempt}): "
                      + first_difference(expected, typed))
            save_proof(page, contact, f"mismatch_attempt_{attempt}", typed)
        else:
            clear_box(page, box)
            raise RuntimeError("couldn't type the message correctly, NOT sent "
                               f"(what was in the box is saved in {proof_path(contact, '.txt')})")

        # Links in the message make WhatsApp load a preview; give it time so
        # Enter isn't swallowed while it loads.
        if "http" in message:
            time.sleep(LINK_PREVIEW_WAIT)

        # Pause as if reviewing the message before sending
        time.sleep(random.uniform(0.8, 2.5))

        save_proof(page, contact, "1_before_send", box_text(box))

        if DRY_RUN:
            write_log(f"✓ [DRY RUN] Message typed for {contact}, not sent")
            clear_box(page, box)
            return SENT

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
        bubble = last_sent_bubble_text(page)
        if bubble is None:
            save_proof(page, contact, "2_sent", "(couldn't read the sent bubble from the chat)")
        else:
            save_proof(page, contact, "2_sent", bubble)
            # The bubble shows formatting instead of the * _ ~ ` marks and adds
            # the time, so check it contains the whole message once those are
            # ignored.
            if same_message(bubble):
                write_log("  ✓ chat shows the exact message")
            else:
                write_log("  ⚠ the last sent bubble differs from the message -- check "
                          + proof_path(contact, ".txt"))
        write_log(f"✓ Sent to {contact}")
        return SENT
    except NotLoggedInError:
        raise
    except Exception as e:
        write_log(f"✗ Failed to send to {contact}: {e}")
        return FAILED


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
    pending, seen, duplicates = [], set(), 0
    for contact in CONTACTS:
        key = contact_key(contact)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        if key not in already_sent:
            pending.append(contact)
    skipped_from_record = len(seen) - len(pending)

    write_log("=" * 50)
    write_log("WhatsApp Bulk Sender (Playwright) - Starting")
    write_log("=" * 50)
    write_log(f"Total contacts: {len(CONTACTS)}")
    if duplicates:
        write_log(f"Ignoring {duplicates} duplicate entr{'y' if duplicates == 1 else 'ies'} in CONTACTS")
    if skipped_from_record:
        write_log(f"Skipping {skipped_from_record} that already got this message (recorded in {SENT_FILE})")
    write_log(f"To send now: {len(pending)}")
    if DRY_RUN:
        write_log("DRY RUN: messages will be typed but NOT sent")
    write_log(f"Delay between messages: {DELAY_RANGE[0]}-{DELAY_RANGE[1]}s (randomized)")
    write_log(f"Log file: {LOG_FILE}")
    write_log("=" * 50)
    write_log("Message preview:\n" + normalize(message))
    write_log("=" * 50)

    if not pending:
        write_log("Nothing to send: every contact already got this message.")
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
        already_count = 0
        failed_contacts = []

        try:
            for i, contact in enumerate(pending, 1):
                write_log(f"\n[{i}/{len(pending)}] Processing: {contact}")
                result = send_message(page, contact)
                if result == SENT:
                    success_count += 1
                    if not DRY_RUN:
                        mark_sent(contact)
                elif result == ALREADY_SENT:
                    already_count += 1
                    mark_sent(contact)
                    continue  # nothing was sent, so no need to wait
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
        write_log(f"↷ Already had this message (skipped): {skipped_from_record + already_count}")
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
