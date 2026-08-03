"""
modules/sentiment.py —— 情感分析引擎（词典+规则）
"""

POSITIVE = {
    "好","赞","优秀","厉害","支持","爱","喜欢","期待","成功","突破","创新",
    "进步","希望","加油","祝贺","恭喜","美丽","精彩","太棒","给力","绝了","宝藏",
    "治愈","温暖","感动","造福","安全","高效","便捷","公平","正义","良心","实惠",
    "开放","透明","利好","友好","和谐","稳定","合理","重磅","惊艳","完美","封神",
    "第一","顶","里程碑","好消息","优惠","免费","福利","惠及","冠军","金牌","获奖",
    "好评","表扬","表彰","就业","减税","补贴","改善","恢复","起飞","爆发","太强了",
    "拍手称快","稳中向好","飞跃","新纪录","实至名归","大快人心","看好","点赞","省心","舒心","给力"
}

NEGATIVE = {
    "差","烂","垃圾","失望","失败","抗议","投诉","黑幕","腐败","不公","歧视",
    "造假","欺骗","隐瞒","泄露","暴力","事故","灾难","死亡","坍塌","爆炸","火灾",
    "地震","洪水","倒闭","破产","裁员","失业","涨价","下跌","暴跌","亏损","违规",
    "罚款","处罚","判刑","停职","下台","撤职","崩了","翻车","塌房","恶心","无耻",
    "抹黑","造谣","谣言","陷阱","坑","焦虑","恐慌","担忧","危机","威胁","风险",
    "隐患","漏洞","脏","乱","抵制","封杀","限制","禁止","致癌","有毒","污染",
    "超标","变质","受害","牺牲","伤亡","失踪","失联","致命","丢人","怒怼","买不起",
    "太丢人","吓人","可怕","坑人"
}

DEGREE = {"非常":2.0,"十分":2.0,"特别":2.0,"极其":2.5,"太":1.8,"很":1.5,"真":1.5,"挺":1.2,"有点":0.6,"相当":1.6}
NEGATION = {"不","没","无","非","未","别","莫","勿","否"}


def analyze(text):
    pos = sum(1 for w in POSITIVE if w in text)
    neg = sum(1 for w in NEGATIVE if w in text)
    for d, m in DEGREE.items():
        for pw in POSITIVE:
            if d + pw in text: pos += 0.5 * m
        for nw in NEGATIVE:
            if d + nw in text: neg += 0.5 * m
    for nw in NEGATION:
        for pw in POSITIVE:
            if nw + pw in text: pos -= 1; neg += 0.5
    total = max(pos + neg, 0.01)
    score = max(-1.0, min(1.0, (pos - neg) / total))
    label = "积极" if score > 0.08 else "消极" if score < -0.08 else "中性"
    return {"score": round(score, 3), "label": label}


def batch_analyze(items):
    for it in items:
        it["sentiment"] = analyze(it.get("title", ""))
    return items


def evaluate(items, ground_truth):
    correct = sum(1 for it in items if it["sentiment"]["label"] == ground_truth.get(it.get("id",""),""))
    return {"accuracy": round(correct / max(len(items), 1), 3), "total": len(items), "correct": correct}
