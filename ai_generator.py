import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import json
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import re
import html

# API kalit faqat muhit o'zgaruvchisidan (Environment Variable) olinadi
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://hnrss.org/frontpage",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
]

SYSTEM_PROMPT = """Siz O'zbekistondagi "Aidevix" IT & AI akademiyasining yetakchi texnik kopirayterisiz.
Quyidagi so'nggi global AI yoki IT yangiligini tahlil qilib, @aidevix Telegram kanali uchun ajoyib, qiziqarli va professional o'zbek tilida post yozib bering.

Post qoidalari va strukturasi:
1. Sarlavha: ⚡ yoki 🤖 emoji bilan boshlanuvchi kuchli, jalb qiluvchi sarlavha.
2. Hook: 1-2 qatorda e'tiborni tortadigan qisqa kirish.
3. Mohiyat: Nima yangilik yuz berdi va u qanday ishlaydi? (lo'nda, 2-3 ta punkt).
4. Dasturchiga/IT ixlosmandiga amaliy foydasi (Why it matters).
5. Xulosa va savol (Call to action).
6. Footer (Aynan shu formatda):
━━━━━━━━━━━━━━━━━━━━━━
Aidevix — AI & Dasturlash O'quv Platformasi 🇺🇿

📢 Kanal: @aidevix
📸 Instagram: @aidevix.uz
🌐 Sayt: aidevix.uz

#AI #TechNews #Dasturlash #Aidevix #VibeCoding

Muhim: Telegram kanali uchun toza, professional va o'qishli matnli post tayyorlang. Sarlavha va asosiy fikrlarni **qalin** qilib bering. Jami matn 800-1500 belgi atrofida bo'lsin. Faqat tayyor post matnini qaytaring, boshqa hech qanday ortiqcha gap yozmang.
"""

def fetch_latest_news():
    for feed_url in RSS_FEEDS:
        try:
            req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                items = root.findall('.//item')
                if not items:
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                    
                for item in items[:10]:
                    title_elem = item.find('title') if item.find('title') is not None else item.find('{http://www.w3.org/2005/Atom}title')
                    desc_elem = item.find('description') if item.find('description') is not None else item.find('{http://www.w3.org/2005/Atom}summary')
                    
                    title = title_elem.text if title_elem is not None and title_elem.text else ""
                    desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                    
                    title = html.unescape(title)
                    desc = html.unescape(re.sub(r'<[^>]+>', '', desc).strip())
                    
                    text_to_check = (title + " " + desc).lower()
                    if any(k in text_to_check for k in ['ai', 'gpt', 'model', 'agent', 'google', 'anthropic', 'meta', 'coding', 'developer', 'software', 'tech', 'gemini']):
                        return {"title": title, "description": desc[:500]}
        except Exception:
            continue
            
    return {
        "title": "Agentic AI va Dasturchilarning yangi ish oqimi",
        "description": "Sun'iy intellekt agentlari endi oddiy chatdan mustaqil ish bajaruvchi avtonom dasturchi hamkasblarga aylanmoqda."
    }

def generate_post_with_gemini(news_item):
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY topilmadi!")
        return None
        
    models = ["gemini-2.5-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest"]
    
    prompt_text = f"Mavzu: {news_item['title']}\nTafsilot: {news_item['description']}\n\nIltimos, ushbu ma'lumot asosida yuqoridagi qoidalarga mos Telegram post yozing."
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT + "\n\n" + prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 600
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload).encode('utf-8')
    
    for model_name in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                res = json.loads(response.read().decode('utf-8'))
                candidates = res.get('candidates', [])
                if candidates:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts:
                        return parts[0].get('text', '').strip()
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
            
    return None

def get_next_post():
    news = fetch_latest_news()
    print(f"Topilgan yangilik: {news['title']}")
    generated_caption = generate_post_with_gemini(news)
    
    if generated_caption:
        return {
            "title": news['title'],
            "caption": generated_caption
        }
    return None

if __name__ == "__main__":
    post = get_next_post()
    if post:
        print("\n=== GENERATSIYA QILINGAN POST ===")
        print(post["caption"])
    else:
        print("Generatsiya qilib bo'lmadi.")
