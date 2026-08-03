"""
modules/hotspot.py —— 热点检测 + 热度预测 + 分词工具
"""

import re
from collections import Counter, defaultdict

STOPWORDS = {"的","了","是","在","和","也","都","就","不","与","及","从","对","以","到",
    "但","而","或","等","这","那","上","下","中","有","人","大","个","一","会","可",
    "着","过","还","吗","啊","吧","呢","哦","如何","怎样","可以","应该","能够","已经",
    "因为","所以","但是","如果","没有","不是","这个","那个","什么","为什么"}


def tokenize(text):
    """简易中文分词"""
    s = re.sub(r'[，。！？；：、\s,.!?;:()\[\]]+', ' ', text)
    words = []
    for seg in s.split():
        for n in (4, 3, 2):
            for i in range(len(seg) - n + 1):
                w = seg[i:i+n]
                if re.search(r'[\u4e00-\u9fff]', w):
                    words.append(w)
    return words


def detect(items):
    """
    热点检测
    返回: (
        [{"keyword": str, "count": int}, ...],  # 关键词 Top15
        [{"name": str, "co_occur": int, "articles": [str,...]}, ...]  # 事件列表
    )
    """
    wc = Counter()
    for it in items:
        for w in tokenize(it["title"]):
            if w not in STOPWORDS and len(w) >= 2:
                wc[w] += 1

    top = wc.most_common(15)
    hotspots = [{"keyword": w, "count": c} for w, c in top]

    events = []
    used = set()
    for w1, _ in top[:10]:
        for w2, _ in top[:10]:
            if w1 >= w2: continue
            cnt = sum(1 for it in items if w1 in it["title"] and w2 in it["title"])
            if cnt >= 3 and w1 not in used and w2 not in used:
                used.update([w1, w2])
                events.append({
                    "name": f"{w1}+{w2}", "co_occur": cnt,
                    "articles": [it["title"] for it in items
                                 if w1 in it["title"] and w2 in it["title"]][:3]
                })
    return hotspots, events


def predict(history):
    """
    热度预测 (简单移动平均 + 趋势)
    history: [day1, day2, ...] 过去N天的值
    返回: [day_n+1, ..., day_n+7] 未来7天预测
    """
    if len(history) < 3:
        return history[-1:] * 7 if history else [0] * 7
    # 移动平均
    avg = sum(history) / len(history)
    # 趋势: 最近3天的平均变化
    diffs = [history[i+1] - history[i] for i in range(max(0, len(history)-4), len(history)-1)]
    trend = sum(diffs) / max(len(diffs), 1)
    preds = []
    last = history[-1]
    for i in range(1, 8):
        last = max(0, last + trend)
        # 衰减
        last = last * (0.85 ** i)
        preds.append(round(last, 1))
    return preds


def predict_top_keywords(hotspots, history_db=None):
    """
    对当前 Top5 关键词做预测
    history_db: {"关键词": [过去N天的值], ...}  (没有就返回模拟值)
    返回: [{"keyword": str, "current": int, "pred_1d": float, "pred_7d": float, "trend": str}, ...]
    """
    results = []
    for h in hotspots[:5]:
        hist = history_db.get(h["keyword"], []) if history_db else []
        if not hist:
            # 用当前值模拟历史
            import random
            hist = [max(0, h["count"] + random.randint(-5, 5)) for _ in range(7)]
        preds = predict(hist)
        trend = "↑" if preds[0] > hist[-1] * 1.1 else "↓" if preds[0] < hist[-1] * 0.9 else "→"
        results.append({
            "keyword": h["keyword"], "current": h["count"],
            "pred_1d": preds[0], "pred_7d": preds[-1], "trend": trend
        })
    return results
