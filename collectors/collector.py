"""
多平台舆情数据采集器 — 8 源 · 并发抓取 · 标题去重 · 摘要提取
用法：python collector.py          → 全部平台
      python collector.py --source 微博热搜,知乎热榜  → 指定平台
"""

import requests
import json
import os
import re
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

now_str = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
#  1. 今日头条热榜
# ============================================================

def fetch_toutiao(count=50):
    url = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        items = []
        for it in data.get("data", []):
            title = it.get("Title", "").strip()
            if title:
                items.append({
                    "title": title, "source": "今日头条",
                    "url": it.get("Url", ""), "time": now_str()
                })
        return items[:count]
    except Exception as e:
        print(f"  [今日头条] 失败: {e}")
        return []


# ============================================================
#  2. 百度热搜
# ============================================================

def fetch_baidu(count=50):
    url = "https://top.baidu.com/board?tab=realtime"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        titles = re.findall(
            r'<div[^>]*class="c-single-text-ellipsis"[^>]*>(.+?)</div>',
            resp.text, re.DOTALL
        )
        return [{"title": t.strip(), "source": "百度热搜", "url": "", "time": now_str()}
                for t in titles[:count] if t.strip()]
    except Exception as e:
        print(f"  [百度热搜] 失败: {e}")
        return []


# ============================================================
#  3. 澎湃新闻热榜
# ============================================================

def fetch_thepaper(count=50):
    url = "https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        items = []
        for it in data.get("data", {}).get("hotNews", []):
            title = it.get("name", "").strip()
            if title:
                items.append({
                    "title": title, "source": "澎湃新闻",
                    "url": "", "time": now_str()
                })
        return items[:count]
    except Exception as e:
        print(f"  [澎湃新闻] 失败: {e}")
        return []


# ============================================================
#  4. 微博热搜 (免 Cookie 代理 API)
# ============================================================

def fetch_weibo(count=50):
    url = "https://api.qqsuu.cn/api/dm-weibohot"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        items = []
        for it in data.get("data", {}).get("list", []):
            title = it.get("hotword", "").strip()
            if title:
                items.append({
                    "title": title, "source": "微博热搜",
                    "url": "", "time": now_str()
                })
        return items[:count]
    except Exception as e:
        print(f"  [微博热搜] 失败: {e}")
        return []


# ============================================================
#  5. 央视新闻
# ============================================================

def fetch_cctv(count=50):
    url = "https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_1.jsonp"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        m = re.search(r'\(({.*})\)', resp.text, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(1))
        items = []
        for it in data.get("data", {}).get("list", []):
            title = it.get("title", "").strip()
            if title:
                items.append({
                    "title": title, "source": "央视新闻",
                    "url": it.get("url", ""), "time": it.get("focus_date", now_str()),
                    "summary": it.get("brief", "")[:200],
                })
        return items[:count]
    except Exception as e:
        print(f"  [央视新闻] 失败: {e}")
        return []


# ============================================================
#  6. 百度新闻搜索 (按热搜关键词检索，拿摘要)
# ============================================================

def fetch_baidu_news(count=50):
    keywords = ["社会", "民生", "教育", "科技", "经济", "政策"]
    all_items = []
    try:
        for kw in keywords[:4]:
            url = f"https://news.baidu.com/ns?word={kw}&pn=0&cl=2&ct=0&tn=news&rn=15"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            # 提取标题
            titles = re.findall(
                r'<h3[^>]*class="news-title[^"]*"[^>]*>\s*<a[^>]*>(.*?)</a>',
                resp.text, re.DOTALL
            )
            # 提取摘要
            abstracts = re.findall(
                r'<div[^>]*class="c-abstract"[^>]*>(.*?)</div>',
                resp.text, re.DOTALL
            )
            clean_titles = [re.sub(r'<[^>]+>', '', t).strip() for t in titles]
            clean_abstracts = [re.sub(r'<[^>]+>', '', a).strip().replace('\n', ' ')
                               for a in abstracts]
            for i, t in enumerate(clean_titles):
                if t:
                    item = {"title": t, "source": "百度新闻",
                            "url": "", "time": now_str(),
                            "keyword": kw}
                    if i < len(clean_abstracts):
                        item["summary"] = clean_abstracts[i][:200]
                    all_items.append(item)
            if len(all_items) >= count:
                break
        return all_items[:count]
    except Exception as e:
        print(f"  [百度新闻] 失败: {e}")
        return []


# ============================================================
#  7. B站热门视频
# ============================================================

def fetch_bilibili(count=50):
    url = "https://api.bilibili.com/x/web-interface/popular?ps=50"
    try:
        resp = requests.get(url, headers={**HEADERS, "Referer": "https://www.bilibili.com/"}, timeout=10)
        data = resp.json()
        items = []
        for v in data.get("data", {}).get("list", []):
            title = v.get("title", "").strip()
            if title:
                items.append({
                    "title": title, "source": "B站热门",
                    "url": f"https://www.bilibili.com/video/{v.get('bvid','')}",
                    "time": now_str(),
                    "summary": v.get("desc", "")[:200],
                })
        return items[:count]
    except Exception as e:
        print(f"  [B站热门] 失败: {e}")
        return []


# ============================================================
#  8. 新浪新闻
# ============================================================

def fetch_sina(count=50):
    url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=50"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()
        items = []
        for it in data.get("result", {}).get("data", []):
            title = it.get("title", "").strip()
            if title:
                items.append({
                    "title": title, "source": "新浪新闻",
                    "url": it.get("url", ""), "time": it.get("ctime", now_str()),
                    "summary": it.get("intro", "")[:200],
                })
        return items[:count]
    except Exception as e:
        print(f"  [新浪新闻] 失败: {e}")
        return []


# ============================================================
#  全部采集器注册
# ============================================================

ALL_SOURCES = {
    "今日头条": fetch_toutiao,
    "百度热搜": fetch_baidu,
    "澎湃新闻": fetch_thepaper,
    "微博热搜": fetch_weibo,
    "央视新闻": fetch_cctv,
    "百度新闻": fetch_baidu_news,
    "B站热门": fetch_bilibili,
    "新浪新闻": fetch_sina,
}


# ============================================================
#  重试机制
# ============================================================

def retry(func, max_retries=2, delay=1.5):
    """API 调用失败自动重试"""
    def wrapper(*args, **kwargs):
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if result:
                    return result
            except Exception as e:
                last_err = e
            if attempt < max_retries:
                time.sleep(delay * (attempt + 1))
        print(f"  [重试 {max_retries} 次均失败] {last_err}")
        return []
    return wrapper


# ============================================================
#  标题去重
# ============================================================

def char_bigrams(text):
    """字符级 2-gram，用于快速相似度计算"""
    return {text[i:i+2] for i in range(len(text)-1)}


def title_similarity(t1, t2):
    """Jaccard 相似度"""
    if not t1 or not t2:
        return 0
    s1, s2 = char_bigrams(t1), char_bigrams(t2)
    if not s1 or not s2:
        return 0
    return len(s1 & s2) / len(s1 | s2)


def deduplicate(items, threshold=0.6):
    """基于标题 Jaccard 相似度去重，保留先出现的"""
    kept = []
    for item in items:
        is_dup = False
        for k in kept:
            if title_similarity(item["title"], k["title"]) >= threshold:
                # 标记重复但保留来源信息
                k.setdefault("cross_sources", set()).add(k["source"])
                k["cross_sources"].add(item["source"])
                is_dup = True
                break
        if not is_dup:
            kept.append(item)
    return kept


# ============================================================
#  正文摘要抓取
# ============================================================

def fetch_summary(url, max_len=200):
    """从 URL 抓取页面摘要（meta description 或正文前 N 字）"""
    if not url or "http" not in url:
        return ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.encoding = "utf-8" if resp.apparent_encoding == "ascii" else resp.apparent_encoding
        html = resp.text
        # 优先取 meta description
        m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html, re.IGNORECASE)
        if not m:
            m = re.search(r'<meta[^>]*content="([^"]+)"[^>]*name="description"', html, re.IGNORECASE)
        if m:
            return m.group(1)[:max_len]
        # 降级：取正文前 N 字
        cleaned = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        cleaned = re.sub(r'<style[^>]*>.*?</style>', '', cleaned, flags=re.DOTALL)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned[:max_len]
    except:
        return ""


def enrich_summaries(items, max_fetch=5):
    """为没有 summary 的条目批量抓取摘要（限制数量避免过慢）"""
    count = 0
    for item in items:
        if not item.get("summary") and item.get("url") and "http" in item.get("url", ""):
            item["summary"] = fetch_summary(item["url"])
            count += 1
            if count >= max_fetch:
                break
    return items


# ============================================================
#  并发聚合入口
# ============================================================

def _fetch_one(name, count):
    """抓取单个源（被线程池调用）"""
    func = ALL_SOURCES.get(name)
    if not func:
        return name, []
    start = time.time()
    try:
        items = retry(func)(count)
        elapsed = time.time() - start
        print(f"  [{name}] {len(items)} 条  ({elapsed:.1f}s)")
        return name, items
    except Exception as e:
        print(f"  [{name}] 失败: {e}")
        return name, []


def collect_all(count=50, sources=None, dedup=True, enrich=True):
    """
    并发采集所有平台
    sources: 要采集的平台列表，默认全部
    dedup:   是否标题去重
    enrich:  是否补充摘要
    """
    if sources is None:
        sources = list(ALL_SOURCES.keys())

    print(f"\n并发采集 {len(sources)} 个平台，每个 {count} 条...\n")
    start = time.time()

    all_items = []
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futures = {pool.submit(_fetch_one, name, count): name for name in sources}
        for future in as_completed(futures):
            _, items = future.result()
            all_items.extend(items)

    elapsed = time.time() - start

    if dedup and all_items:
        before = len(all_items)
        all_items = deduplicate(all_items)
        print(f"\n去重: {before} → {len(all_items)} 条  (合并 {before - len(all_items)} 条)")
        for item in all_items:
            cs = item.get("cross_sources")
            if cs and len(cs) > 1:
                item["cross_sources"] = list(cs)

    if enrich:
        all_items = enrich_summaries(all_items)

    print(f"\n总耗时: {elapsed:.1f}s | 最终: {len(all_items)} 条")
    return all_items


def save_to_json(items, filename="raw.json"):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"\n总计 {len(items)} 条，已保存到 {path}")
    srcs = Counter(i["source"] for i in items)
    for s, c in srcs.most_common():
        print(f"  {s}: {c} 条")
    return path


# ============================================================
#  模拟数据兜底
# ============================================================

def generate_mock_data():
    from demo.demo import generate_mock_data as gmd
    return gmd()


# ============================================================
#  主入口
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  多平台舆情数据采集器 (8 源)")
    print("=" * 50)
    print()

    # 命令行参数：python collector.py --source 微博热搜,知乎热榜
    sources = list(ALL_SOURCES.keys())
    if "--source" in sys.argv:
        idx = sys.argv.index("--source")
        sources = [s.strip() for s in sys.argv[idx + 1].split(",")]
        invalid = [s for s in sources if s not in ALL_SOURCES]
        if invalid:
            print(f"未知来源: {invalid}")
            print(f"可选: {list(ALL_SOURCES.keys())}")
            sys.exit(1)

    count = 50
    if "--count" in sys.argv:
        idx = sys.argv.index("--count")
        count = int(sys.argv[idx + 1])

    items = collect_all(count=count, sources=sources)

    if not items:
        print("\n[警告] 所有平台采集失败，切换模拟数据")
        items = generate_mock_data()

    save_to_json(items, "raw.json")
