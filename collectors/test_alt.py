import requests, re, json, sys

h = {'User-Agent': 'Mozilla/5.0 Chrome/120.0.0.0'}

# 试36氪
try:
    r = requests.get('https://www.36kr.com/newsflashes', headers=h, timeout=10)
    m = re.search(r'window\.initialState\s*=\s*(\{.*?\});', r.text, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        items = data.get('newsflashCatalogData', {}).get('data', {}).get('newsflashes', [])
        print(f'36kr: {len(items)} 条')
        for it in items[:5]:
            t = it.get("title", "")[:60]
            print(f'  {t}')
    else:
        print('36kr: initialState not found')
except Exception as e:
    print(f'36kr: FAIL {e}')

# 试网易新闻
try:
    r = requests.get('https://c.m.163.com/nc/article/headline/T1348647853363/0-40.html',
                     headers=h, timeout=10)
    data = r.json()
    items = data.get('T1348647853363', [])
    print(f'\n网易新闻: {len(items)} 条')
    for it in items[:5]:
        print(f"  {it.get('title','')[:60]}  {it.get('source','')}")
except Exception as e:
    print(f'网易新闻: FAIL {e}')
