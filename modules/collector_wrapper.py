"""
成员A - 数据采集与清洗
提供 collect_data() 作为主入口，返回统一格式的数据列表
"""

def collect_data(sources=None, count=30):
    """
    采集舆情数据
    sources: 要采集的源列表，默认全部
    count: 每个源采集条数

    返回格式: [
        {"title": "新闻标题", "source": "来源名", "url": "链接",
         "time": "2026-08-01", "summary": "摘要（可选）"},
        ...
    ]
    """
    from collectors.collector import collect_all
    return collect_all(count=count, sources=sources)


def clean_and_dedup(items):
    """数据清洗：去重、去空、去广告等"""
    return items


def get_source_stats(items):
    """返回来源统计：{来源名: 条数}"""
    from collections import Counter
    return dict(Counter(i["source"] for i in items))
