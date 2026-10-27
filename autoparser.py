
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

FOREIGN_RSS = [
    "https://www.tomshardware.com/feeds/all",
    "https://www.gsmarena.com/rss-news-reviews.php3",
    "https://www.theverge.com/rss/index.xml"
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
        text_clean = re.sub(r'[\r\n]+', ' ', text)
        translated = translator.translate(text_clean[:1800])
        return translated if translated else text
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def is_tech_or_home_news(title):
    t = title.lower()
    allowed_keywords = [
        'phone', 'iphone', 'samsung', 'pixel', 'xiaomi', 'gpu', 'rtx', 'cpu', 
        'intel', 'amd', 'laptop', 'tablet', 'screen', 'display', 'camera', 
        'gadget', 'chip', 'memory', 'ssd', 'ps5', 'xbox', 'nintendo', 'smart',
        'vacuum', 'robot', 'coffee', 'kitchen', 'appliance', 'home', 'washer',
        'смартфон', 'процессор', 'видеокарта', 'экран', 'камера', 'пылесос', 
        'умный дом', 'техника', 'кухня', 'чайник', 'утюг'
    ]
    forbidden = ['policy', 'court', 'lawsuit', 'government', 'election', 'politics', 'deal', 'stock market']
    if any(f in t for f in forbidden):
        return False
    return any(kw in t for kw in allowed_keywords)

def detect_category(title):
    t = title.lower()
    if any(w in t for w in ['vacuum', 'robot', 'coffee', 'kitchen', 'appliance', 'home', 'washer', 'пылесос', 'дом', 'кухня']):
        return 'Бытовая техника'
    elif any(w in t for w in ['phone', 'iphone', 'samsung', 'pixel', 'смартфон', 'xiaomi']):
        return 'Смартфоны'
    elif any(w in t for w in ['gpu', 'rtx', 'cpu', 'intel', 'amd', 'pc', 'laptop', 'ноутбук', 'ssd']):
        return 'Железо'
    else:
        return 'Гаджеты'

def generate_sitemap_and_rss(posts):
    domain = "https://piar0zz.github.io/site-tech/"
    
    # Sitemap.xml
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url>\n    <loc>{domain}</loc>\n    <changefreq>hourly</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
    for p in posts:
        sitemap += f'  <url>\n    <loc>{domain}#{p["slug"]}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
    sitemap += '</urlset>'
    with open('sitemap.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap)

    # RSS.xml для Pinterest и агрегаторов
    rss = '<?xml version="1.0" encoding="UTF-8" ?>\n'
    rss += '<rss version="2.0">\n<channel>\n'
    rss += '  <title>ТехноОбзор — Тесты и обзоры техники</title>\n'
    rss += f'  <link>{domain}</link>\n'
    rss += '  <description>Независимые обзоры смартфонов, железа, гаджетов и бытовой техники</description>\n'
    rss += '  <language>ru-RU</language>\n'
    
    for p in posts[:30]:
        rss += '  <item>\n'
        rss += f'    <title><![CDATA[{p["title"]}]]></title>\n'
        rss += f'    <link>{domain}#{p["slug"]}</link>\n'
        rss += f'    <guid>{domain}#{p["slug"]}</guid>\n'
        rss += f'    <description><![CDATA[{p["description"]}]]></description>\n'
        rss += f'    <category>{p["category"]}</category>\n'
        rss += f'    <pubDate>{p["date"]}</pubDate>\n'
        rss += '  </item>\n'
        
    rss += '</channel>\n</rss>'
    with open('rss.xml', 'w', encoding='utf-8') as f:
        f.write(rss)
    
    print("SEO Карты сайта и RSS успешно обновлены!")

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

                for item in items[:5]:
                    title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
                    raw_title = title_elem.text if title_elem is not None else ''

                    if not is_tech_or_home_news(raw_title):
                        continue

                    desc_elem = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                    raw_desc = desc_elem.text if desc_elem is not None else ''
                    clean_desc = clean_html(raw_desc)

                    img_url = ""
                    enclosure = item.find('enclosure')
                    if enclosure is not None and 'image' in enclosure.attrib.get('type', ''):
                        img_url = enclosure.attrib.get('url', '')
                    else:
                        media = item.find('{http://search.yahoo.com/mrss/}content')
                        if media is not None:
                            img_url = media.attrib.get('url', '')

                    if len(raw_title) > 10:
                        ru_title = safe_translate(raw_title)
                        ru_desc = safe_translate(clean_desc[:600])
                        
                        slug = slugify(ru_title)
                        category = detect_category(ru_title)

                        if slug and slug not in existing_slugs:
                            img_html = f'<div class="mb-6"><img src="{img_url}" alt="{ru_title}" class="w-full h-auto rounded-2xl object-cover max-h-[450px] shadow-lg border border-slate-800"></div>' if img_url else ''
                            
                            seo_content = f"""
                            {img_html}
                            <p class="text-base md:text-lg font-medium text-slate-200 mb-6"><strong>Главное о новинке:</strong> {ru_desc}</p>
                            
                            <h2 class="text-lg md:text-xl font-bold text-white mt-6 mb-3">🛠️ Технические характеристики и особенности</h2>
                            <p class="mb-4">Анализ инженерного исполнения показывает, что разработчики уделили особое внимание надежности, эргономике и производительности в реальных сценариях эксплуатации.</p>
                            
                            <h2 class="text-lg md:text-xl font-bold text-white mt-6 mb-3">📊 Результаты независимого тестирования</h2>
                            <p class="mb-4">В ходе испытаний модель продемонстрировала стабильные показатели энергоэффективности и эффективное распределение ресурсов.</p>
                            <ul class="list-disc pl-5 space-y-2 mb-6 text-slate-300">
                                <li>Высокое качество сборки и современные материалы корпуса.</li>
                                <li>Оптимизированное энергопотребление под нагрузкой.</li>
                                <li>Улучшенные алгоритмы работы и расширенный функционал.</li>
                            </ul>

                            <h2 class="text-lg md:text-xl font-bold text-white mt-6 mb-3">💡 Итоговый вердикт редакции</h2>
                            <p>Рассматриваемое устройство уверенно держит конкурентную планку в своем сегменте рынка.</p>
                            """

                            new_post = {
                                "slug": slug,
                                "title": ru_title,
                                "description": ru_desc[:200] + "...",
                                "content": seo_content,
                                "category": category,
                                "date": datetime.now().strftime("%d.%m.%Y")
                            }
                            posts.insert(0, new_post)
                            existing_slugs.add(slug)
                            new_count += 1
        except Exception as e:
            print(f"Ошибка с {url}: {e}")

    posts = posts[:150]
    with open('posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    generate_sitemap_and_rss(posts)
    print(f"Добавлено полноценных статей: {new_count}")

if __name__ == "__main__":
    fetch_and_translate_rss()
