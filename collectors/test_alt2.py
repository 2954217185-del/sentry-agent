import requests, re, json

h = {'User-Agent': 'Mozilla/5.0 Chrome/120.0.0.0'}

# 试1：网易新闻不同的API
try:
    r = requests.get('https://c.m.163.com/nc/article/list/T1348647853363/0-20.html', headers=h, timeout=10)
    data = r.json()
    items = data.get('T1348647853363', [])
    print(f'网易新闻: {len(items)} 条')
    for it in items[:5]:
        print(f"  {it.get('title','')[:60]}")
except Exception as e:
    print(f'网易新闻: FAIL {e}')

# 试2：新浪新闻二级
try:
    r = requests.get('https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2510&num=30', headers=h, timeout=10)
    data = r.json()
    items = data.get('result',{}).get('data',[])
    print(f'\n新浪新闻(社会): {len(items)} 条')
    for it in items[:5]:
        print(f"  {it.get('title','')[:60]}")
except Exception as e:
    print(f'新浪新闻: FAIL {e}')

# 试3：央视新闻
try:
    r = requests.get('https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_1.jsonp', headers=h, timeout=10)
    text = r.text
    m = re.search(r'\((.*)\)', text, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        items = data.get('data',{}).get('list',[])
        print(f'\n央视新闻: {len(items)} 条')
        for it in items[:5]:
            t = it.get('title', '')
        print(f"  {t[:60]}")
except Exception as e:
    print(f'央视新闻: FAIL {e}')

# 试4：凤凰网
try:
    r = requests.get('https://i.ifeng.com/api/newslist?type=GN&page=1&pagesize=20', headers=h, timeout=10)
    data = r.json()
    print(f'\n凤凰网: {len(data)} 条' if isinstance(data, list) else f'\n凤凰网: keys={list(data.keys())[:5]}')
except Exception as e:
    print(f'凤凰网: FAIL {e}')
