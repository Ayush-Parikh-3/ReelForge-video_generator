import requests
import re
import urllib.parse
from PIL import Image
import io

def search_wikimedia_image(query: str, width: int = 1280):
    # Extract core keywords
    words = re.findall(r'\b[A-Za-z]{3,}\b', query)
    stop_words = {'the', 'and', 'with', 'from', 'into', 'shot', 'view', 'scene', 'cinematic', 'high', 'detail', 'photorealistic', 'resolution', 'camera', 'dramatic', 'lighting'}
    filtered = [w for w in words if w.lower() not in stop_words]
    clean_q = " ".join(filtered[:4])
    if not clean_q:
        clean_q = query[:30]

    url = 'https://commons.wikimedia.org/w/api.php'
    params = {
        'action': 'query',
        'generator': 'search',
        'gsrsearch': clean_q,
        'gsrnamespace': 6,
        'gsrlimit': 6,
        'prop': 'imageinfo',
        'iiprop': 'url',
        'iiurlwidth': width,
        'format': 'json'
    }
    headers = {'User-Agent': 'VividAIVideoBot/1.0 (contact@vividai.local)'}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            pages = r.json().get('query', {}).get('pages', {})
            for pid, p in pages.items():
                title = p.get('title', '').lower()
                # filter out audio/pdf/svg
                if title.endswith(('.jpg', '.jpeg', '.png')):
                    info = p.get('imageinfo', [{}])[0]
                    thumb = info.get('thumburl') or info.get('url')
                    if thumb:
                        return thumb
    except Exception as e:
        print('Wikimedia search err:', e)
    return None

test_queries = [
    "A cascading river of digital text fragments turning into numbers in a warehouse",
    "An overhead view of a star-filled cosmos where stars morph into colorful vector dots",
    "Layers of transformers checking words using attention heads in data center",
    "Liquid gradient descent flowing over weight matrices in computer chip",
    "Luminous misty studio screen morphing into glowing flowing text"
]

for q in test_queries:
    img_url = search_wikimedia_image(q)
    print("Query:", q[:40], "...")
    print(" -> Found:", img_url)
