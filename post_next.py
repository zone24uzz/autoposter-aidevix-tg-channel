import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error
import re
import html

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from ai_generator import get_next_post

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8832388019:AAFaj7_zY7MepFKXrhYBHd15oawP3Ehq2N0")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1003047427642")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "8357557157")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_QUEUE_FILE = os.path.join(BASE_DIR, "posts_queue.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
HISTORY_MD_FILE = os.path.join(BASE_DIR, "POSTS_HISTORY.md")

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

def append_to_markdown_history(title, caption, slot, post_type):
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"""
## 📅 {now_str} — {title}
**Slot:** `{slot}` | **Turi:** `{post_type}`

```markdown
{caption}
```

---
"""
    if not os.path.exists(HISTORY_MD_FILE):
        header = "# 📚 Aidevix Telegram Kanali Postlar Tarixi va Arxiv\n\nUshbu faylda barcha e'lon qilingan va AI tomonidan generatsiya qilingan postlar avtomatik saqlanib boradi.\n\n---\n"
        with open(HISTORY_MD_FILE, 'w', encoding='utf-8') as f:
            f.write(header)
            
    with open(HISTORY_MD_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)

def format_to_html(text):
    # HTML maxsus belgilarini xavfsiz escape qilish
    escaped = html.escape(text)
    # **qalin matn** va __qalin matn__ -> <b>...</b>
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)
    escaped = re.sub(r'__(.+?)__', r'<b>\1</b>', escaped)
    # `kod matni` -> <code>...</code>
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    return escaped

def send_message(chat_id, text):
    """
    Telegramga rasmsiz, toza va chiroyli formatlangan matnli post yuborish.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # 1-urinish: Chiroyli HTML format bilan yuborish
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
        print(f"HTML Parse/HTTP Error ({e.code}): {err_msg}. Plain text sifatida qayta urinilmoqda...")
    except Exception as e:
        print(f"HTML yuborishda xatolik: {e}")
        
    # 2-urinish (Fallback): Formatlarsiz oddiy matn (plain text) ko'rinishida yuborish
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
    except urllib.error.HTTPError as e:
        print(f"Plain text HTTP Error ({e.code}): {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"Plain text yuborishda xatolik: {e}")
        return False

def main():
    queue = load_json(POSTS_QUEUE_FILE, [])
    pending_posts = [p for p in queue if p.get("status") != "published"]
    
    target_post = None
    slot = datetime.datetime.now().strftime("%H:%M")
    post_type = "queued"
    
    # 1. Navbatdagi postni tekshiramiz
    if pending_posts:
        target_post = pending_posts[0]
        title = target_post.get("title", "Yangi post")
        caption = target_post.get("caption", "")
        slot = target_post.get("time_slot", slot)
    else:
        # 2. Navbat tugasa, Gemini orqali jonli yangilik
        print("Navbat tugagan. Gemini AI orqali jonli yangilik olinmoqda...")
        ai_post = get_next_post()
        if ai_post:
            title = ai_post.get("title", "AI Yangilik")
            caption = ai_post.get("caption", "")
            post_type = "ai_generated"
        else:
            print("Yangilik generatsiya qilib bo'lmadi.")
            sys.exit(1)
            
    print(f"Post tayyorlandi: '{title}' (Rasmsiz, toza matn ko'rinishida)")
        
    # 🔔 DARHOL ADMIN LICHKASIGA (Telegram Bot orqali) YUBORISH
    if ADMIN_CHAT_ID:
        admin_prefix = f"🔔 [YANGI POST CHIQARILMOQDA — {slot}]\n\n"
        send_message(ADMIN_CHAT_ID, admin_prefix + caption)
        print(f"Admin ({ADMIN_CHAT_ID}) ga darhol Telegram bot orqali xabar yuborildi! 📲")
        
    # Kanalga joylash (Rasmsiz, matnli post)
    success = send_message(CHANNEL_ID, caption)
    
    if success:
        print(f"Post muvaffaqiyatli kanalga joylandi! 🎉")
        if target_post:
            target_post["status"] = "published"
            target_post["published_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_json(POSTS_QUEUE_FILE, queue)
            
        history = load_json(HISTORY_FILE, [])
        history.append({
            "title": title,
            "published_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": post_type
        })
        save_json(HISTORY_FILE, history)
        
        # Markdown faylga arxivlash
        append_to_markdown_history(title, caption, slot, post_type)
        print("Post 'POSTS_HISTORY.md' arxiv fayliga yozib qo'yildi! 📝")
    else:
        print("Kanalga joylashda xatolik yuz berdi!")
        sys.exit(1)

if __name__ == "__main__":
    main()
