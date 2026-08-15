import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import time
from send_previews import send_photo, POSTS_QUEUE_FILE, DEFAULT_IMAGE, USER_CHAT_ID

with open(POSTS_QUEUE_FILE, 'r', encoding='utf-8') as f:
    queue = json.load(f)

p = queue[1] # Post 2
prefix = f"📌 [BUGUNGI POST PREVIEW — {p['time_slot']}]\n\n"
caption = (prefix + p['caption'])[:1020]

for attempt in range(3):
    time.sleep(1)
    success = send_photo(USER_CHAT_ID, p.get('image_path', DEFAULT_IMAGE), caption)
    if success:
        print("Post 2 muvaffaqiyatli yetib bordi! ✅")
        break
    else:
        print(f"Urinish {attempt+1} muvaffaqiyatsiz, qayta urinilmoqda...")
