import urllib.request
import xml.etree.ElementTree as ET
import json
import os
import re
from datetime import datetime

try:
    from deep_translator import GoogleTranslator
except ImportError:
    os.system('pip install deep-translator')
    from deep_translator import GoogleTranslator

# Зарубежные RSS-источники
FOREIGN_RSS = [
    "https://www.theverge.com/rss/index.xml",
    "https://www.engadget.com/rss.xml",
    "https://www.tomshardware.com/feeds/all",
    "https://www.gsmarena.com/rss-news-reviews.php3"
]

translator = GoogleTranslator(source='en', target='ru')

def slugify(text):
    translit = {
        'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z',
        'и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r',
        'с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'c','ч':'ch','ш':'sh','щ':'shch',
        'ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya'
    }
    text = text.lower()
    res = []
    for char in text:
        if char in translit:
            res.append(translit[char])
        elif char.isalnum():
            res.append(char)
        elif char in [' ', '-']:
            res.append('-')
    slug = ''.join(res)
    return re.sub(r'-+', '-', slug).strip('-')[:60]

def clean_html(raw_html):
    return re.sub(r'<[^>]+>', '', raw_html).strip()

def safe_translate(text):
    if not text:
        return ""
    try:
        return translator.translate(text[:2000])
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def fetch_and_translate_rss():
    posts = []
    
    if os.path.exists('posts.json'):
        with open('posts.json', 'r', encoding='utf-8') as f:
            try:
                posts = json.load(f)
            except:
                posts = []

    existing_slugs = {p['slug'] for p in posts}
    new_count = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for url in FOREIGN_RSS:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                
                items = root.findall('.//item')
                if not items:
                    items = root.findall('.//{http://www.w3.org/2005/Atom}entry')

                for item in items[:4]:
                    title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                    raw_title = title_elem.text if title_elem is not None else ''

                    desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    raw_desc = desc_elem.text if desc_elem is not None else ''
                    clean_desc = clean_html(raw_desc)

                    if len(raw_title) > 10:
                        ru_title = safe_translate(raw_title)
                        ru_desc = safe_translate(clean_desc[:400])
                        
                        slug = slugify(ru_title)

                        if slug and slug not in existing_slugs:
                            seo_content = f"""
                            <p><strong>Подробный разбор и обзор устройства:</strong> {ru_desc}</p>
                            <h3>Основные особенности и тесты</h3>
                            <p>Специалисты профильной лаборатории изучили заявленные характеристики новинки. Устройство показывает отличную стабильность под нагрузкой и сбалансированные параметры автономности.</p>
                            <p><em>Итог тестирования:</em> Интересное решение в своем классе, заслуживающее внимания покупателей.</p>
                            """

                            new_post = {
                                "slug": slug,
                                "title": ru_title,
                                "description": ru_desc[:200] + "...",
                                "content": seo_content,
                                "category": "Зарубежные тесты",
                                "date": datetime.now().strftime("%d.%m.%Y")
                            }
                            posts.insert(0, new_post)
                            existing_slugs.add(slug)
                            new_count += 1
        except Exception as e:
            print(f"Ошибка при работе с {url}: {e}")

    posts = posts[:150]

    with open('posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"Готово! Добавлено {new_count} новых статей.")

if __name__ == "__main__":
    fetch_and_translate_rss()
