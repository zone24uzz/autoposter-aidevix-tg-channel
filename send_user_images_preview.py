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

IMAGES_DIR = r"D:\Jarvis\aidevix_autoposter\images"
IMG_1 = os.path.join(IMAGES_DIR, "post1.jpg")
IMG_2 = os.path.join(IMAGES_DIR, "post2.jpg")
IMG_3 = os.path.join(IMAGES_DIR, "post3.jpg")

with open(POSTS_QUEUE_FILE, 'r', encoding='utf-8') as f:
    queue = json.load(f)

# Update queue with user's real images
queue[0]["image_path"] = IMG_1
queue[1]["image_path"] = IMG_2
queue[2]["image_path"] = IMG_3

with open(POSTS_QUEUE_FILE, 'w', encoding='utf-8') as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)

print("posts_queue.json yangilandi: Siz yuklagan rasmlar biriktirildi!")

# Send previews to user
for idx, p in enumerate(queue[:3]):
    prefix = f"✨ [SIZNING RASMINGIZ BILAN PREVIEW — {p['time_slot']}]\n\n"
    caption = (prefix + p['caption'])[:1020]
    time.sleep(1.5)
    
    img_path = p["image_path"]
    if not os.path.exists(img_path):
        print(f"Xato: {img_path} topilmadi!")
        continue
        
    res = send_photo(USER_CHAT_ID, img_path, caption)
    print(f"Post {idx+1} ({p['time_slot']}): {'Yuborildi ✅' if res else 'Xato ❌'}")
