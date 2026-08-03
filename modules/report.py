"""
modules/report.py —— 报告生成子 Agent
"""

import os
from datetime import datetime
from collections import Counter

BASE = os.path.dirname(os.path.dirname(__file__))


def generate(items, hotspots, events, attr_stats):
    """
    生成 Markdown 舆情日报
    返回: (文件路径, 报告内容字符串)
    """
    total = len(items)
    sl = Counter(i["sentiment"]["label"] for i in items)
    srcs = Counter(i["source"] for i in items)
    today = datetime.now().strftime("%Y%m%d")

    r = f"# 舆情日报 {datetime.now().strftime('%Y-%m-%d')}\n\n"
    r += f"> {total} 条数据 · {', '.join(srcs.keys())}\n\n---\n\n"

    r += "## 情感概览\n| 类型 | 数量 | 占比 |\n|---|---|---|\n"
    for k in ["积极", "消极", "中性"]:
        r += f"| {k} | {sl.get(k,0)} | {sl.get(k,0)/total*100:.1f}% |\n"

    r += "\n## 热点关键词 Top 10\n| 关键词 | 热度 |\n|---|---|\n"
    for h in hotspots[:10]:
        r += f"| {h['keyword']} | {h['count']} |\n"

    if events:
        r += f"\n## 热点事件 ({len(events)})\n\n"
        for e in events:
            r += f"### {e['name']}（共现 {e['co_occur']} 次）\n"
            for a in e["articles"]: r += f"- {a}\n"
            r += "\n"

    r += "\n## 来源分布\n| 来源 | 数量 |\n|---|---|\n"
    for s, c in srcs.most_common():
        r += f"| {s} | {c} |\n"

    r += "\n## 敏感属性\n| 类别 | 提及 | Top词汇 |\n|---|---|---|\n"
    for cat, info in attr_stats.items():
        ts = ", ".join(f"{k}({v})" for k, v in info["top"])
        r += f"| {cat} | {info['total']} | {ts} |\n"

    negs = [i for i in items if i["sentiment"]["label"] == "消极"]
    if negs:
        r += "\n## 消极舆情样本\n\n"
        for it in negs[:5]:
            r += f"- [{it['source']}] {it['title']} (得分: {it['sentiment']['score']})\n"

    r += "\n---\n*Sentry 舆情监测 Agent 自动生成*"

    path = os.path.join(BASE, "demo", f"report_{today}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(r)
    return path, r
