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
import mimetypes

BOT_TOKEN = "8832388019:AAFaj7_zY7MepFKXrhYBHd15oawP3Ehq2N0"
CHANNEL_ID = "-1003047427642" # @aidevix
ADMIN_CHAT_ID = "8357557157"   # Foydalanuvchi

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
POSTS_QUEUE_FILE = os.path.join(BASE_DIR, "posts_queue.json")
DEFAULT_IMAGE = os.path.join(BASE_DIR, "images", "post1.png")

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

def send_photo(chat_id, photo_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    if not os.path.exists(photo_path):
        # Fallback to any available post image in images dir
        for ext in [".png", ".jpg", ".jpeg"]:
            alt = os.path.join(BASE_DIR, "images", f"post1{ext}")
            if os.path.exists(alt):
                photo_path = alt
                break
                
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
        print(f"[{datetime.datetime.now()}] HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Send error: {e}")
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
            print(f"[{datetime.datetime.now()}] '{title}' posti @aidevix kanaliga nashr qilinmoqda...")
            
            # Auto detect if png or jpg exists
            img = target_post.get("image_path")
            if not img or not os.path.exists(img):
                img = os.path.join(BASE_DIR, "images", "post1.png")
                if not os.path.exists(img):
                    img = os.path.join(BASE_DIR, "images", "post1.jpg")
                    
            success = send_photo(CHANNEL_ID, img, target_post.get("caption", ""))
            
            # Admin ga xabarnoma
            send_photo(ADMIN_CHAT_ID, img, f"✅ [Avtomatik e'lon qilindi: {slot_str}]\n\n" + target_post.get("caption", ""))
            
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
