import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8832388019:AAFaj7_zY7MepFKXrhYBHd15oawP3Ehq2N0")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1003047427642")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "8357557157")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_QUEUE_FILE = os.path.join(BASE_DIR, "posts_queue.json")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
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

def send_photo(chat_id, photo_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    if not os.path.exists(photo_path):
        # Fallback
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
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"Send error: {e}")
        return False

def main():
    queue = load_json(POSTS_QUEUE_FILE, [])
    pending_posts = [p for p in queue if p.get("status") != "published"]
    
    if not pending_posts:
        print("Navbatda yangi nashr qilinmagan post yo'q!")
        sys.exit(0)
        
    target_post = pending_posts[0]
    title = target_post.get("title", "Yangi post")
    slot = target_post.get("time_slot", "07:45")
    
    print(f"Nashr qilinmoqda: '{title}'...")
    img = target_post.get("image_path")
    if not img or not os.path.exists(img):
        # Local rel path
        img = os.path.join(BASE_DIR, "images", f"post{target_post.get('order', 1)}.jpg")
        if not os.path.exists(img):
            img = os.path.join(BASE_DIR, "images", f"post{target_post.get('order', 1)}.png")
            if not os.path.exists(img):
                img = DEFAULT_IMAGE
                
    success = send_photo(CHANNEL_ID, img, target_post.get("caption", ""))
    
    # Admin ga ham xabar
    if ADMIN_CHAT_ID:
        send_photo(ADMIN_CHAT_ID, img, f"✅ [GitHub Actions orqali chiqarildi: {slot}]\n\n" + target_post.get("caption", ""))
        
    if success:
        print(f"Post muvaffaqiyatli kanalga joylandi! 🎉")
        target_post["status"] = "published"
        target_post["published_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_json(POSTS_QUEUE_FILE, queue)
        
        history = load_json(HISTORY_FILE, [])
        history.append({
            "id": target_post.get("id"),
            "title": title,
            "published_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_json(HISTORY_FILE, history)
    else:
        print("Kanalga joylashda xatolik yuz berdi!")
        sys.exit(1)

if __name__ == "__main__":
    main()
