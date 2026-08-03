"""
modules/collector.py —— 多平台数据采集 + 清洗 + 去重
只负责采集逻辑，不涉及前端
"""

import requests
import json
import os
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "collectors", "data")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

now = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _retry(func, max_retries=2, delay=1.5):
    def wrapper(*a, **kw):
        for attempt in range(max_retries + 1):
            try:
                r = func(*a, **kw)
                if r: return r
            except: pass
            if attempt < max_retries: time.sleep(delay * (attempt + 1))
        return []
    return wrapper


# ---- 8 个采集源 ----

def _fetch_toutiao(n):
    try: r=requests.get("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("Title","").strip(),"source":"今日头条","url":i.get("Url",""),"time":now()} for i in r.json().get("data",[]) if i.get("Title","").strip()][:n]

def _fetch_baidu(n):
    try: r=requests.get("https://top.baidu.com/board?tab=realtime",headers=HEADERS,timeout=8)
    except: return []
    titles=re.findall(r'<div[^>]*class="c-single-text-ellipsis"[^>]*>(.+?)</div>',r.text,re.DOTALL)
    return [{"title":t.strip(),"source":"百度热搜","url":"","time":now()} for t in titles[:n] if t.strip()]

def _fetch_thepaper(n):
    try: r=requests.get("https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("name","").strip(),"source":"澎湃新闻","url":"","time":now()} for i in r.json().get("data",{}).get("hotNews",[]) if i.get("name","").strip()][:n]

def _fetch_weibo(n):
    try: r=requests.get("https://api.qqsuu.cn/api/dm-weibohot",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("hotword","").strip(),"source":"微博热搜","url":"","time":now()} for i in r.json().get("data",{}).get("list",[]) if i.get("hotword","").strip()][:n]

def _fetch_cctv(n):
    try: r=requests.get("https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_1.jsonp",headers=HEADERS,timeout=8)
    except: return []
    m=re.search(r"\(({.*})\)",r.text,re.DOTALL)
    if not m: return []
    return [{"title":i.get("title","").strip(),"source":"央视新闻","url":i.get("url",""),"time":i.get("focus_date",""),"summary":i.get("brief","")[:200]} for i in json.loads(m.group(1)).get("data",{}).get("list",[]) if i.get("title","").strip()][:n]

def _fetch_baidu_news(n):
    try:
        items=[]
        for kw in ["社会","民生","教育","科技"][:3]:
            r=requests.get(f"https://news.baidu.com/ns?word={kw}&pn=0&rn=20",headers=HEADERS,timeout=8)
            titles=re.findall(r'<h3[^>]*class="news-title[^"]*"[^>]*>\s*<a[^>]*>(.*?)</a>',r.text,re.DOTALL)
            abs_=re.findall(r'<div[^>]*class="c-abstract"[^>]*>(.*?)</div>',r.text,re.DOTALL)
            for i,t in enumerate([re.sub(r'<[^>]+>','',t).strip() for t in titles]):
                if t:
                    item={"title":t,"source":"百度新闻","url":"","time":now()}
                    if i<len(abs_): item["summary"]=re.sub(r'<[^>]+>','',abs_[i]).strip()[:200]
                    items.append(item)
            if len(items)>=n: break
        return items[:n]
    except: return []

def _fetch_bilibili(n):
    try: r=requests.get("https://api.bilibili.com/x/web-interface/popular?ps=50",headers={**HEADERS,"Referer":"https://www.bilibili.com/"},timeout=8)
    except: return []
    return [{"title":v.get("title","").strip(),"source":"B站热门","url":f"https://www.bilibili.com/video/{v.get('bvid','')}","time":now()} for v in r.json().get("data",{}).get("list",[]) if v.get("title","").strip()][:n]

def _fetch_sina(n):
    try: r=requests.get("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=50",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("title","").strip(),"source":"新浪新闻","url":i.get("url",""),"time":i.get("ctime",""),"summary":i.get("intro","")[:200]} for i in r.json().get("result",{}).get("data",[]) if i.get("title","").strip()][:n]


ALL_SOURCES = {
    "今日头条": _fetch_toutiao, "百度热搜": _fetch_baidu,
    "澎湃新闻": _fetch_thepaper, "微博热搜": _fetch_weibo,
    "央视新闻": _fetch_cctv, "百度新闻": _fetch_baidu_news,
    "B站热门": _fetch_bilibili, "新浪新闻": _fetch_sina,
}


# ---- 标题去重 ----

def _char_bigrams(text):
    return {text[i:i+2] for i in range(len(text)-1)}

def _title_similarity(t1, t2):
    s1, s2 = _char_bigrams(t1), _char_bigrams(t2)
    if not s1 or not s2: return 0
    return len(s1 & s2) / len(s1 | s2)

def deduplicate(items, threshold=0.6):
    kept = []
    for item in items:
        dup = False
        for k in kept:
            if _title_similarity(item["title"], k["title"]) >= threshold:
                k.setdefault("cross_sources", set()).add(k["source"])
                k["cross_sources"].add(item["source"])
                dup = True; break
        if not dup: kept.append(item)
    for item in kept:
        cs = item.get("cross_sources")
        if cs and len(cs) > 1: item["cross_sources"] = list(cs)
    return kept


# ---- 主入口 ----

def collect_all(sources=None, count=30, dedup=True):
    if sources is None: sources = list(ALL_SOURCES.keys())
    all_items = []
    with ThreadPoolExecutor(max_workers=min(6, len(sources))) as pool:
        futures = {pool.submit(_retry(ALL_SOURCES[name]), count): name for name in sources if name in ALL_SOURCES}
        for f in as_completed(futures):
            name = futures[f]
            try:
                items = f.result()
                all_items.extend(items)
            except: pass
    if dedup: all_items = deduplicate(all_items)
    return all_items


def load_local():
    path = os.path.join(DATA_DIR, "raw.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_local(items):
    path = os.path.join(DATA_DIR, "raw.json")
    safe_items = []
    for it in items:
        item = dict(it)
        if isinstance(item.get("cross_sources"), set):
            item["cross_sources"] = list(item["cross_sources"])
        safe_items.append(item)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(safe_items, f, ensure_ascii=False, indent=2)
    return path
