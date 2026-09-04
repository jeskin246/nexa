import urllib.request, urllib.parse, re

for sp in ['&sp=CAM%253D', '&sp=EgIQAQ%253D%253D']:
    url = f'https://www.youtube.com/results?search_query=dsa{sp}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            vids = re.findall(r'(?:"videoId":\s*"|/watch\?v=)([a-zA-Z0-9_-]{11})', html)
            print(f'{sp}: top ID: {vids[0] if vids else None}')
    except Exception as e:
        print(f'{sp}: error {e}')
