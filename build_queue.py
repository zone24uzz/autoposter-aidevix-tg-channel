import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import re

MD_PATH = r"c:\Users\user\Downloads\IT yangilik va tayyor Telegram postlari.md"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTS_QUEUE_FILE = os.path.join(BASE_DIR, "posts_queue.json")
DEFAULT_IMAGE = os.path.join(r"C:\Users\user\.gemini\antigravity-cli\brain\d50f1280-c654-494f-98e4-0330669fe408", "clean_agent_banner_1786755705506.jpg")

FOOTER = """
━━━━━━━━━━━━━━━━━━━━━━
Aidevix — AI & Dasturlash O'quv Platformasi 🇺🇿

📢 Kanal: @aidevix
📸 Instagram: @aidevix.uz
🌐 Sayt: aidevix.uz

#AI #TechNews #Dasturlash #Aidevix #VibeCoding"""

def parse_markdown_posts():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = re.split(r'\n##\s+\d+\)\s+', content)
    posts = []
    
    time_slots = ["07:45", "12:20", "19:45"]
    
    for idx, sec in enumerate(sections[1:], start=1):
        lines = sec.strip().split('\n')
        title = lines[0].strip()
        
        bq_match = re.search(r'\*\*Tayyor post\*\*\s*\n\n(.*?)(?=\n\n\*\*Manbalar:\*\*|\n\n---|\Z)', sec, re.DOTALL)
        if not bq_match:
            continue
            
        raw_post = bq_match.group(1).strip()
        clean_lines = []
        for line in raw_post.split('\n'):
            line = line.strip()
            if line.startswith('>'):
                line = line[1:].strip()
            clean_lines.append(line)
            
        clean_post = '\n'.join(clean_lines).strip()
        
        full_caption = f"⚡ {title}\n\n{clean_post}\n{FOOTER}"
        
        if len(full_caption) > 1020:
            full_caption = full_caption[:1015] + "..."
            
        slot = time_slots[(idx - 1) % len(time_slots)]
        
        posts.append({
            "id": f"post_{idx}",
            "order": idx,
            "title": title,
            "time_slot": slot,
            "image_path": DEFAULT_IMAGE,
            "caption": full_caption,
            "status": "pending"
        })
        
    return posts

def main():
    posts = parse_markdown_posts()
    print(f"Jami {len(posts)} ta yangilik muvaffaqiyatli ajratib olindi!")
    
    with open(POSTS_QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
        
    print(f"Barcha 13 ta post '{POSTS_QUEUE_FILE}' ga saqlandi!")

if __name__ == "__main__":
    main()
