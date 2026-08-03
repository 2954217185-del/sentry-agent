"""
成员C - 热点检测 + 热度预测 + GNN公平性

需实现:
  detect_hotspots(items) -> (关键词列表, 事件列表)
  predict_heat(keyword_history) -> 未来N天预测值
  build_gnn_graph(items) -> PyG Data 对象
  counterfactual_analysis(graph, model, item, attribute) -> 偏见效应
"""

def detect_hotspots(items, time_window_hours=24):
    """
    热点检测
    返回: (
        [{"keyword": "xx", "count": 10}, ...],  # 关键词Top15
        [{"name": "A+B", "co_occur": 5, "articles": [...]}, ...]  # 事件
    )
    """
    # TODO: 成员C实现
    pass


def predict_heat(history):
    """
    热度预测 (Holt-Winters 或 ARIMA)
    history: 过去N天的词频序列 [day1_count, day2_count, ...]
    返回: [day_n+1_pred, day_n+2_pred, ...]  + 置信区间
    """
    # TODO: 成员C实现
    pass


def build_sentiment_graph(items):
    """
    构建舆情图 (PyG)
    节点 = 新闻, 边 = 关键词共现
    返回: torch_geometric.data.Data 对象
    """
    # TODO: 成员C实现
    pass


def counterfactual_fairness(model, graph, item, sensitive_attr):
    """
    反事实公平性分析
    替换 item 中的敏感属性后，重跑 GNN 预测
    返回: {"original_score": xx, "cf_score": xx, "bias": xx}
    """
    # TODO: 成员C实现
    pass
