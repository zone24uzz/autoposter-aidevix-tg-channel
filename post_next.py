import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error

from ai_generator import get_next_post

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8832388019:AAFaj7_zY7MepFKXrhYBHd15oawP3Ehq2N0")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1003047427642")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "8357557157")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_QUEUE_FILE = os.path.join(BASE_DIR, "posts_queue.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
HISTORY_MD_FILE = os.path.join(BASE_DIR, "POSTS_HISTORY.md")
DEFAULT_IMAGE = os.path.join(BASE_DIR, "images", "post1.png")

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

def send_photo(chat_id, photo_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    if not photo_path or not os.path.exists(photo_path):
        for ext in [".png", ".jpg", ".jpeg"]:
            alt = os.path.join(BASE_DIR, "images", f"post1{ext}")
            if os.path.exists(alt):
                photo_path = alt
                break
                
    if not os.path.exists(photo_path):
        img_dir = os.path.join(BASE_DIR, "images")
        if os.path.exists(img_dir):
            files = [os.path.join(img_dir, f) for f in os.listdir(img_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            if files:
                photo_path = files[0]
                
    with open(photo_path, 'rb') as f:
        file_bytes = f.read()
        
    filename = os.path.basename(photo_path)
    mime_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"
    
    body = bytearray()
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode('utf-8'))
    body.extend(f'{chat_id}\r\n'.encode('utf-8'))
    
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode('utf-8'))
    body.extend(caption.encode('utf-8'))
    body.extend(b'\r\n')
    
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="photo"; filename="{filename}"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: {mime_type}\r\n\r\n'.encode('utf-8'))
    body.extend(file_bytes)
    body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    
    req = urllib.request.Request(url, data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("ok", False)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"Send error: {e}")
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
        img = target_post.get("image_path")
        slot = target_post.get("time_slot", slot)
    else:
        # 2. Navbat tugasa, Gemini orqali jonli yangilik
        print("Navbat tugagan. Gemini AI orqali jonli yangilik olinmoqda...")
        ai_post = get_next_post()
        if ai_post:
            title = ai_post.get("title", "AI Yangilik")
            caption = ai_post.get("caption", "")
            img = DEFAULT_IMAGE
            post_type = "ai_generated"
        else:
            print("Yangilik generatsiya qilib bo'lmadi.")
            sys.exit(1)
            
    print(f"Post tayyorlandi: '{title}'")
    if not img or not os.path.exists(img):
        img = DEFAULT_IMAGE
        
    # 🔔 DARHOL ADMIN LICHKASIGA (Telegram Bot orqali) YUBORISH
    if ADMIN_CHAT_ID:
        admin_prefix = f"🔔 [YANGI POST TOPILDI VA CHIQARILDI — {slot}]\n\n"
        admin_caption = (admin_prefix + caption)[:1020]
        send_photo(ADMIN_CHAT_ID, img, admin_caption)
        print(f"Admin ({ADMIN_CHAT_ID}) ga darhol Telegram bot orqali xabar yuborildi! 📲")
        
    # Kanalga joylash
    success = send_photo(CHANNEL_ID, img, caption)
    
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
