import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import time
import datetime
import json
import urllib.request
import urllib.parse
import urllib.error
import re
import html

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8832388019:AAFaj7_zY7MepFKXrhYBHd15oawP3Ehq2N0")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1003047427642") # @aidevix
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "8357557157")       # Foydalanuvchi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
POSTS_QUEUE_FILE = os.path.join(BASE_DIR, "posts_queue.json")

SCHEDULE_TIMES = ["07:45", "12:20", "19:45"]

def load_json(filepath, default):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_to_html(text):
    escaped = html.escape(text)
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)
    escaped = re.sub(r'__(.+?)__', r'<b>\1</b>', escaped)
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    return escaped

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    html_text = format_to_html(text)
    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            if res.get("ok", False):
                return True
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        print(f"HTML Parse Error ({e.code}): {err_msg}")
    except Exception as e:
        print(f"HTML Send error: {e}")
        
    # Plain text fallback
    try:
        plain_payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True
        }
        plain_data = json.dumps(plain_payload).encode('utf-8')
        plain_req = urllib.request.Request(url, data=plain_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(plain_req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("ok", False)
    except Exception as e:
        print(f"Plain text Send error: {e}")
        return False

def get_next_scheduled_event():
    now = datetime.datetime.now()
    
    events = []
    for item in SCHEDULE_TIMES:
        h, m = map(int, item.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target >= now:
            events.append((target, item))
            
    if not events:
        tomorrow = now + datetime.timedelta(days=1)
        h, m = map(int, SCHEDULE_TIMES[0].split(":"))
        target = tomorrow.replace(hour=h, minute=m, second=0, microsecond=0)
        events.append((target, SCHEDULE_TIMES[0]))
        
    events.sort(key=lambda x: x[0])
    return events[0]

def main_loop():
    print(f"[{datetime.datetime.now()}] Aidevix AutoPoster ishga tushdi! 🚀")
    print(f"Jadval vaqtlari: {', '.join(SCHEDULE_TIMES)}")
    
    history = load_json(HISTORY_FILE, [])
    
    while True:
        queue = load_json(POSTS_QUEUE_FILE, [])
        pending_posts = [p for p in queue if p.get("status") != "published"]
        
        print(f"[{datetime.datetime.now()}] Navbatdagi kutilayotgan postlar soni: {len(pending_posts)} ta")
        
        next_time, slot_str = get_next_scheduled_event()
        now = datetime.datetime.now()
        wait_seconds = max(0, int((next_time - now).total_seconds()))
        
        print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Keyingi post vaqti: {next_time.strftime('%Y-%m-%d %H:%M:%S')} ({wait_seconds} soniya kutiladi)")
        
        if wait_seconds > 0:
            time.sleep(wait_seconds)
        
        # Vaqt yetib keldi
        queue = load_json(POSTS_QUEUE_FILE, [])
        target_post = None
        for p in queue:
            if p.get("status") != "published":
                target_post = p
                break
                
        if target_post:
            title = target_post.get("title", "Yangi post")
            print(f"[{datetime.datetime.now()}] '{title}' posti @aidevix kanaliga rasmsiz matn sifatida nashr qilinmoqda...")
            
            caption = target_post.get("caption", "")
            success = send_message(CHANNEL_ID, caption)
            
            # Admin ga xabarnoma
            send_message(ADMIN_CHAT_ID, f"✅ [Avtomatik e'lon qilindi: {slot_str}]\n\n" + caption)
            
            if success:
                print(f"[{datetime.datetime.now()}] Muvaffaqiyatli kanalga joylandi! 🎉")
                target_post["status"] = "published"
                target_post["published_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_json(POSTS_QUEUE_FILE, queue)
                
                history.append({
                    "id": target_post.get("id"),
                    "title": title,
                    "slot": slot_str,
                    "published_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                save_json(HISTORY_FILE, history)
            else:
                print(f"[{datetime.datetime.now()}] Joylashda xatolik yuz berdi!")
        else:
            print(f"[{datetime.datetime.now()}] Navbatda yangi post qolmagan!")
            
        time.sleep(10)

if __name__ == "__main__":
    main_loop()
