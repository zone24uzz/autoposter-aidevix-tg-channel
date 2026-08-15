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

BRAIN_DIR = r"C:\Users\user\.gemini\antigravity-cli\brain\d50f1280-c654-494f-98e4-0330669fe408"
IMG_1 = os.path.join(BRAIN_DIR, "gpt_work_banner_1786758513314.jpg")
IMG_2 = os.path.join(BRAIN_DIR, "gemini_flash_banner_1786758527259.jpg")
IMG_3 = os.path.join(BRAIN_DIR, "claude_opus_banner_1786758538294.jpg")

with open(POSTS_QUEUE_FILE, 'r', encoding='utf-8') as f:
    queue = json.load(f)

# Update images
queue[0]["image_path"] = IMG_1
queue[1]["image_path"] = IMG_2
queue[2]["image_path"] = IMG_3

with open(POSTS_QUEUE_FILE, 'w', encoding='utf-8') as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)

print("posts_queue.json yangilandi: har bir postga o'zining unikal 3D rasmi biriktirildi!")

# Send to user
for idx, p in enumerate(queue[:3]):
    prefix = f"🎨 [YANGI RASMLI PREVIEW — {p['time_slot']}]\n\n"
    caption = (prefix + p['caption'])[:1020]
    time.sleep(1)
    res = send_photo(USER_CHAT_ID, p["image_path"], caption)
    print(f"Post {idx+1} ({p['time_slot']}): {'Yuborildi ✅' if res else 'Xato ❌'}")
