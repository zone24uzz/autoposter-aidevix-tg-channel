import os
import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from autoposter import send_message, CHANNEL_ID, ADMIN_CHAT_ID, BASE_DIR, HISTORY_FILE, POSTS_QUEUE_FILE, load_json, save_json
import datetime

queue = load_json(POSTS_QUEUE_FILE, [])
pending_posts = [p for p in queue if p.get("status") != "published"]

if not pending_posts:
    print("Navbatda nashr qilinmagan post yo'q!")
    sys.exit(0)

target_post = pending_posts[0]
title = target_post.get("title")
caption = target_post.get("caption", "")

print(f"'{title}' posti @aidevix kanaliga rasmsiz matn sifatida yuborilmoqda...")
success = send_message(CHANNEL_ID, caption)

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
    
    # Admin ga tasdiq
    send_message(ADMIN_CHAT_ID, f"🎉 [Kanalga muvaffaqiyatli joylandi!]\n\n" + caption)
else:
    print("Kanalga yuborishda xatolik yuz berdi! Bot @aidevix kanalida admin ekanligini tekshiring.")
