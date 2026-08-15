import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import urllib.request
import urllib.error

BOT_TOKEN = "8832388019:AAFaj7_zY7MepFKXrhYBHd15oawP3Ehq2N0"
USER_CHAT_ID = "8357557157"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_QUEUE_FILE = os.path.join(BASE_DIR, "posts_queue.json")
DEFAULT_IMAGE = os.path.join(r"C:\Users\user\.gemini\antigravity-cli\brain\d50f1280-c654-494f-98e4-0330669fe408", "clean_agent_banner_1786755705506.jpg")

def send_photo(chat_id, photo_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    
    with open(photo_path, 'rb') as f:
        file_bytes = f.read()
    
    body = bytearray()
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'.encode('utf-8'))
    body.extend(f'{chat_id}\r\n'.encode('utf-8'))
    
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="caption"\r\n\r\n'.encode('utf-8'))
    body.extend(caption.encode('utf-8'))
    body.extend(b'\r\n')
    
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="photo"; filename="banner.jpg"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: image/jpeg\r\n\r\n'.encode('utf-8'))
    body.extend(file_bytes)
    body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    
    req = urllib.request.Request(url, data=body)
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res.get("ok", False)
    except Exception as e:
        print(f"Send error: {e}")
        return False

def main():
    with open(POSTS_QUEUE_FILE, 'r', encoding='utf-8') as f:
        queue = json.load(f)
        
    today_posts = queue[:3]
    print(f"Bugungi 3 ta post foydalanuvchiga ({USER_CHAT_ID}) jo'natilmoqda...")
    
    for p in today_posts:
        prefix = f"📌 [BUGUNGI POST PREVIEW — {p['time_slot']}]\n\n"
        caption = prefix + p['caption']
        if len(caption) > 1024:
            caption = caption[:1020] + "..."
            
        success = send_photo(USER_CHAT_ID, p.get("image_path", DEFAULT_IMAGE), caption)
        print(f"Post {p['order']} ({p['time_slot']}): {'Yuborildi ✅' if success else 'Xato ❌'}")

if __name__ == "__main__":
    main()
