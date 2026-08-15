import os
import sys
import json
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from send_previews import send_photo, POSTS_QUEUE_FILE, USER_CHAT_ID

with open(POSTS_QUEUE_FILE, 'r', encoding='utf-8') as f:
    queue = json.load(f)

p = queue[1]
IMG_2 = r"D:\Jarvis\aidevix_autoposter\images\post2.jpg"
prefix = f"✨ [SIZNING RASMINGIZ BILAN PREVIEW — {p['time_slot']}]\n\n"
caption = (prefix + p['caption'])[:1020]

for attempt in range(3):
    time.sleep(1.5)
    success = send_photo(USER_CHAT_ID, IMG_2, caption)
    if success:
        print("Post 2 muvaffaqiyatli yetib bordi! ✅")
        break
    else:
        print(f"Urinish {attempt+1} muvaffaqiyatsiz, qayta urinilmoqda...")
