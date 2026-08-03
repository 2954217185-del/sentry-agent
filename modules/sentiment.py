"""
成员B - 情感分析引擎

需实现的函数:
  analyze_sentiment(text) -> {"score": float, "label": str}
  batch_analyze(items) -> 给每条数据加上 sentiment 字段
  evaluate_accuracy(items, ground_truth) -> 准确率报告

进阶:
  detect_stance(text) -> 立场检测（支持/反对/中立）
  fine_grained_emotion(text) -> 细粒度情绪（愤怒/焦虑/讽刺等）
"""

def analyze_sentiment(text):
    """
    输入: 文本字符串
    输出: {"score": -1.0~1.0 的得分, "label": "积极"/"消极"/"中性"}
    要求: 词典+规则实现，不要调LLM
    """
    # TODO: 成员B实现
    pass


def batch_analyze(items):
    """批量分析，在原数据上添加 sentiment 字段"""
    for it in items:
        it["sentiment"] = analyze_sentiment(it["title"])
    return items


def evaluate_accuracy(items, ground_truth):
    """
    评估准确率
    items: 已标注 sentiment 的数据
    ground_truth: 人工标注的正确标签 {"news_id": "积极/消极/中性"}
    返回: {"accuracy": 0.85, "precision": {...}, "recall": {...}}
    """
    # TODO: 成员B实现
    pass
