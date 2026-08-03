"""
成员D - 报告生成 + 话题聚类 + 跨平台对比

需实现:
  generate_daily_report(items, hotspots, events) -> Markdown 字符串
  cluster_topics(items) -> 话题分组结果
  cross_platform_compare(items, topic) -> 平台对比矩阵
"""

def generate_daily_report(items, hotspots, events, attr_stats):
    """生成 Markdown 格式舆情日报"""
    # TODO: 成员D实现
    pass


def cluster_topics(items, n_clusters=10):
    """
    话题聚类 (层次聚类/Agglomerative)
    返回: {
        "话题名": {
            "keywords": [...],
            "articles": [...],
            "sentiment_dist": {"积极": N, ...},
            "sensitive_attrs": {...}
        }, ...
    }
    """
    # TODO: 成员D实现
    pass


def cross_platform_compare(items, topic_keywords):
    """
    跨平台叙事对比
    同一话题在不同平台的措辞和情感差异
    返回: {
        "微博": {"avg_sentiment": 0.3, "keywords": [...], "sample": [...]},
        "知乎": {"avg_sentiment": -0.1, "keywords": [...], "sample": [...]},
        ...
    }
    """
    # TODO: 成员D实现
    pass
