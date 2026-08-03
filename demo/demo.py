"""
课题41：舆情监测与热点分析 Agent —— 端到端 Demo（零依赖版）
运行：python demo.py
"""

import json
import os
import re
import sys
from datetime import datetime
from collections import Counter, defaultdict

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "collectors", "data")


# ============================================================
#  简易中文分词（不依赖 jieba）
# ============================================================

def simple_tokenize(text):
    """简易中文分词：按标点切句，然后 2-4 字滑窗切词。"""
    sentences = re.split(r'[，。！？、；：""' + r"'" + r'（）\s,.!?;:"' + r"'" + r'()\[\]]+', text)
    words = []
    for sent in sentences:
        for n in (4, 3, 2):
            for i in range(len(sent) - n + 1):
                w = sent[i:i+n]
                if re.search(r'[\u4e00-\u9fff]', w):  # 至少含一个汉字
                    words.append(w)
    return words + sentences  # 也保留完整短句


# ============================================================
#  Step 0：数据加载
# ============================================================

def load_data():
    raw_path = os.path.join(DATA_DIR, "raw.json")
    if os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        print(f"[数据加载] 从 data/raw.json 加载 {len(items)} 条")
        return items
    print("[数据加载] raw.json 不存在，使用内置模拟数据")
    return generate_mock_data()


def generate_mock_data():
    data = []
    srcs = ["知乎热榜", "微博热搜", "百度热搜"]
    mock = [
        # 知乎
        ("高校食堂涨价引学生抗议", ["高校", "食堂", "涨价", "抗议"]),
        ("AI会取代程序员吗从业5年真实感受", ["AI", "程序员", "取代"]),
        ("年轻人越来越不愿走亲戚现象背后", ["年轻人", "走亲戚"]),
        ("考研人数下降学历还值钱吗", ["考研", "学历", "下降"]),
        ("毕业后第一份工作选错能补救吗", ["毕业", "工作"]),
        ("某公司996工作制引发社会讨论", ["996", "加班"]),
        ("研究生导师压榨学生为何屡禁不止", ["导师", "压榨", "学生"]),
        ("30岁转行来得及吗有哪些方向", ["30岁", "转行"]),
        ("预制菜进校园引家长担忧", ["预制菜", "校园", "家长"]),
        ("一线城市房价还会继续跌吗", ["房价", "一线城市", "下跌"]),
        ("自媒体行业现在还能入行吗", ["自媒体", "入行"]),
        ("冷门但高薪的职业方向推荐", ["冷门", "高薪", "职业"]),
        ("如何看待某明星深夜发文回应", ["明星", "回应"]),
        ("新能源汽车真的比燃油车省钱吗", ["新能源", "省钱"]),
        ("短视频平台对青少年影响如何", ["短视频", "青少年"]),
        ("某品牌虚假宣传被重罚消费者拍手称快", ["虚假宣传", "重罚"]),
        ("高校运动会的开幕式太惊艳了给力", ["运动会", "惊艳"]),
        ("某城市入选全球最宜居城市真实至名归", ["宜居", "城市"]),
        ("多地高温预警太热了大家注意防暑", ["高温", "防暑"]),
        ("某地夜市的特色小吃街火爆值得一去", ["夜市", "小吃"]),
        # 微博
        ("某地发生地震暂无人员伤亡祈福平安", ["地震", "伤亡", "祈福"]),
        ("某高校论文抄袭被撤销学位太丢人", ["论文抄袭", "学位", "丢人"]),
        ("某综艺因争议内容被停播观众失望", ["综艺", "停播", "失望"]),
        ("某APP泄露用户隐私引发社会恐慌", ["泄露", "隐私", "恐慌"]),
        ("某网红直播带货翻车遭网友怒怼", ["网红", "直播", "翻车", "怼"]),
        ("某公司大规模裁员员工拉横幅维权", ["裁员", "维权"]),
        ("某电影票房突破30亿创造新纪录", ["电影", "票房", "纪录"]),
        ("某餐厅食品安全问题被曝光停业整顿", ["食品安全", "曝光", "停业"]),
        ("某明星夫妇宣布离婚网友热议不断", ["明星", "离婚", "热议"]),
        ("某小区物业不作为业主集体投诉", ["物业", "投诉"]),
        ("某地暴雨致多地受灾救援正在进行", ["暴雨", "受灾", "救援"]),
        ("某教师因不当言论被停职调查", ["教师", "停职", "调查"]),
        ("某品牌新品发布售价惊人网友直呼买不起", ["新品", "售价", "买不起"]),
        ("某高校宿舍限电引学生不满集体抗议", ["宿舍", "限电", "抗议"]),
        ("某省发布人才引进新政力度空前", ["人才引进", "新政"]),
        # 百度
        ("国家统计局公布上半年经济数据稳中向好", ["经济", "稳中向好"]),
        ("某高官违纪违法被立案调查大快人心", ["高官", "违纪", "调查"]),
        ("世界卫生组织发布最新健康警告", ["健康", "警告"]),
        ("某城市出台楼市新政二手房市场受影响", ["楼市", "新政"]),
        ("某大学排名出炉清华北大依旧领先", ["大学排名"]),
        ("暑期旅游旺季热门线路一票难求", ["旅游", "旺季"]),
        ("国内油价迎来年内最大降幅可喜可贺", ["油价", "降幅"]),
        ("某科技公司发布新一代芯片性能飞跃", ["芯片", "性能", "飞跃"]),
        ("科学家发现新型材料有望改变能源行业", ["新材料", "能源"]),
        ("某地出台垃圾分类新规市民热议", ["垃圾分类", "新规"]),
        ("航天员完成太空授课活动获广泛好评", ["航天员", "好评"]),
        ("某省高考分数线公布考生家长紧张关注", ["高考", "分数线"]),
        ("新能源汽车销量突破预期行业前景看好", ["新能源", "销量", "看好"]),
        ("某国际赛事中国队斩获多枚金牌太强了", ["赛事", "金牌", "太强了"]),
        ("某知名企业宣布大规模招聘计划就业利好", ["招聘", "就业", "利好"]),
    ]
    for i, (title, _) in enumerate(mock):
        data.append({
            "title": title,
            "source": srcs[i % 3],
            "url": "",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    return data[:120]


# ============================================================
#  Step 1：情感分析
# ============================================================

POSITIVE = {
    "好", "赞", "优秀", "厉害", "支持", "爱", "喜欢", "期待", "成功",
    "突破", "创新", "进步", "希望", "加油", "祝贺", "恭喜", "美丽",
    "精彩", "太棒", "给力", "绝了", "宝藏", "治愈", "温暖", "感动",
    "造福", "安全", "高效", "便捷", "公平", "正义", "良心", "实惠",
    "开放", "透明", "利好", "友好", "和谐", "稳定", "合理",
    "重磅", "惊艳", "完美", "封神", "天花板", "第一", "顶",
    "创造历史", "里程碑", "好消息", "优惠", "免费", "福利", "惠及",
    "冠军", "金牌", "获奖", "好评", "表扬", "表彰", "荣升", "上调",
    "就业", "减税", "补贴", "改善", "恢复", "复苏", "起飞", "爆发",
    "好评", "太强了", "拍手称快", "可喜可贺", "稳中向好", "飞跃",
    "新纪录", "实至名归", "值得一去", "大快人心", "看好", "点赞",
}
NEGATIVE = {
    "差", "烂", "垃圾", "失望", "失败", "抗议", "投诉", "黑幕",
    "腐败", "不公", "歧视", "造假", "欺骗", "隐瞒", "泄露", "暴力",
    "事故", "灾难", "死亡", "坍塌", "爆炸", "火灾", "地震", "洪水",
    "倒闭", "破产", "裁员", "失业", "涨价", "下跌", "暴跌", "亏损",
    "违规", "罚款", "处罚", "判刑", "停职", "下台", "撤职",
    "崩了", "翻车", "塌房", "恶心", "无耻", "卑鄙", "讽刺",
    "抹黑", "造谣", "谣言", "阴谋", "陷阱", "坑",
    "焦虑", "恐慌", "担忧", "危机", "威胁", "风险", "隐患", "漏洞",
    "脏", "乱", "差评", "抵制", "封杀", "限制", "禁止",
    "致癌", "有毒", "污染", "超标", "细菌", "发霉", "变质",
    "受害", "牺牲", "伤亡", "失踪", "失联", "致命",
    "丢人", "怒怼", "恐慌", "买不起", "失望", "太丢人",
}
DEGREE_DICT = {
    "非常": 2.0, "十分": 2.0, "特别": 2.0, "极其": 2.5, "太": 1.8,
    "很": 1.5, "真": 1.5, "挺": 1.2, "有点": 0.6, "相当": 1.6,
}
NEGATION_DICT = {"不", "没", "无", "非", "未", "别", "莫", "勿", "否"}


def analyze_sentiment(text):
    matched = []
    neg = 0
    pos = 0

    for w in POSITIVE:
        if w in text:
            pos += 1
            if any(d + w in text for d in DEGREE_DICT):
                pos += 0.5
    for w in NEGATIVE:
        if w in text:
            neg += 1
            if any(d + w in text for d in DEGREE_DICT):
                neg += 0.5

    # 否定词处理
    for negw in NEGATION_DICT:
        for posw in POSITIVE:
            if negw + posw in text:
                pos -= 1
                neg += 0.5
        for negw2 in NEGATIVE:
            if negw + negw2 in text:
                neg -= 0.5

    total = pos + neg + 0.01
    score = (pos - neg) / max(total, 1)
    score = max(-1.0, min(1.0, score))

    if score > 0.08:
        label = "积极"
    elif score < -0.08:
        label = "消极"
    else:
        label = "中性"

    return {"score": round(score, 3), "label": label}


def run_sentiment(items):
    print(f"\n{'='*50}\n  Step 1：情感分析\n{'='*50}")
    for item in items:
        item["sentiment"] = analyze_sentiment(item["title"])
    labels = Counter(i["sentiment"]["label"] for i in items)
    total = len(items)
    for k in ["积极", "消极", "中性"]:
        print(f"    {k}: {labels.get(k, 0)} ({labels.get(k,0)/total*100:.1f}%)")
    return items


# ============================================================
#  Step 2：热点检测
# ============================================================

def detect_hotspots(items):
    print(f"\n{'='*50}\n  Step 2：热点检测\n{'='*50}")

    stopwords = {
        "的", "了", "是", "在", "和", "也", "都", "就", "不", "与", "及",
        "从", "对", "以", "到", "但", "而", "或", "等", "这", "那",
        "上", "下", "中", "有", "人", "大", "个", "一", "会", "可",
        "着", "过", "还", "吗", "啊", "吧", "呢", "哦", "如何", "怎样",
        "可以", "应该", "能够", "已经", "因为", "所以", "但是", "如果",
        "没有", "不是", "这个", "那个", "什么", "为什么", "怎么办",
    }

    word_counter = Counter()
    for item in items:
        words = simple_tokenize(item["title"])
        for w in words:
            if w not in stopwords and len(w) >= 2:
                word_counter[w] += 1

    top_words = word_counter.most_common(15)
    hotspots = [{"keyword": w, "count": c} for w, c in top_words]

    print("  Top 5 热点关键词:")
    for h in hotspots[:5]:
        print(f"    {h['keyword']} — {h['count']} 次")

    # 共现聚合事件
    events = []
    used = set()
    for w1, _ in top_words[:10]:
        for w2, _ in top_words[:10]:
            if w1 >= w2:
                continue
            cnt = sum(1 for it in items if w1 in it["title"] and w2 in it["title"])
            if cnt >= 3 and w1 not in used and w2 not in used:
                used.update([w1, w2])
                events.append({
                    "name": f"{w1} + {w2}",
                    "keywords": [w1, w2],
                    "co_occur": cnt,
                    "articles": [it["title"] for it in items
                                 if w1 in it["title"] and w2 in it["title"]][:3]
                })

    print(f"\n  热点事件（共现≥3次）: {len(events)} 个")
    for e in events[:5]:
        print(f"    {e['name']}: 共现 {e['co_occur']} 次")
    return hotspots, events


# ============================================================
#  Step 3：敏感属性检测
# ============================================================

SENSITIVE_PATTERNS = {
    "性别": ["女子", "男子", "女性", "男性", "女司机", "男司机", "女教师", "男主", "女主",
             "女神", "男神", "女孩", "男孩", "妇女", "性别", "男女"],
    "地域": ["北京", "上海", "广州", "深圳", "河南", "山东", "东北", "南方", "北方",
             "农村", "城市", "乡镇", "海外", "国内", "某省", "某市", "某县", "一线城市"],
    "年龄": ["年轻人", "老年人", "老人", "00后", "90后", "80后", "大学生",
             "中学生", "小学生", "儿童", "少年", "中年", "青年", "未成年", "30岁"],
    "职业": ["外卖员", "快递员", "程序员", "工人", "教师", "医生", "护士", "工人",
             "警察", "公务员", "农民工", "学生", "主播", "网红", "艺人", "明星",
             "老板", "创业者", "白领", "蓝领", "客服", "保安", "保姆", "航天员"],
    "社会身份": ["穷人", "富人", "底层", "精英", "体制内", "海归", "海龟",
               "本地人", "外地人", "租客", "房奴", "独生子女", "残疾人", "单亲",
               "留守", "孕妇", "家长"],
}


def detect_sensitive_attrs(items):
    print(f"\n{'='*50}\n  Step 3：敏感属性检测\n{'='*50}")
    attr_counter = defaultdict(Counter)
    for item in items:
        for cat, patterns in SENSITIVE_PATTERNS.items():
            for p in patterns:
                if p in item["title"]:
                    attr_counter[cat][p] += 1
    stats = {}
    for cat, counter in attr_counter.items():
        total_hits = sum(counter.values())
        top = counter.most_common(3)
        stats[cat] = {"total": total_hits, "top": top}
        print(f"  {cat}: {total_hits} 条 — {', '.join(f'{k}({v})' for k,v in top)}")
    return stats


# ============================================================
#  Step 4：报告生成子 Agent
# ============================================================

def generate_report(items, hotspots, events, attr_stats):
    print(f"\n{'='*50}\n  Step 4：报告生成子 Agent\n{'='*50}")

    total = len(items)
    sent_labels = Counter(i["sentiment"]["label"] for i in items)
    sources = Counter(i["source"] for i in items)
    today = datetime.now().strftime("%Y年%m月%d日")

    report = f"""# 舆情日报 {today}

> 自动生成 · 数据来源：{', '.join(sources.keys())}
> 监测条数：{total} 条

---

## 📊 情感概览

| 类型 | 数量 | 占比 |
|------|------|------|
| 积极 | {sent_labels.get('积极', 0)} | {sent_labels.get('积极', 0)/total*100:.1f}% |
| 消极 | {sent_labels.get('消极', 0)} | {sent_labels.get('消极', 0)/total*100:.1f}% |
| 中性 | {sent_labels.get('中性', 0)} | {sent_labels.get('中性', 0)/total*100:.1f}% |
"""

    neg_ratio = sent_labels.get("消极", 0) / total if total > 0 else 0
    if neg_ratio > 0.4:
        report += f"### ⚠️ 负面预警\n\n消极情绪占比 {neg_ratio*100:.1f}%，超过 40% 警戒线。\n\n"

    report += "## 🔥 热点关键词 Top 10\n\n| 关键词 | 次数 |\n|------|------|\n"
    for h in hotspots[:10]:
        report += f"| {h['keyword']} | {h['count']} |\n"

    if events:
        report += f"\n## 🫧 热点事件（{len(events)}个）\n\n"
        for e in events[:5]:
            report += f"### {e['name']}（共现{e['co_occur']}次）\n"
            for a in e["articles"]:
                report += f"- {a}\n"
            report += "\n"

    report += "## 📡 来源分布\n\n| 来源 | 数量 |\n|------|------|\n"
    for src, cnt in sources.most_common():
        report += f"| {src} | {cnt} |\n"

    report += "\n## 🏷️ 敏感属性统计\n\n| 类别 | 提及次数 | Top词汇 |\n|------|------|------|\n"
    for cat, info in attr_stats.items():
        top_str = ", ".join(f"{k}({v})" for k, v in info["top"])
        report += f"| {cat} | {info['total']} | {top_str} |\n"

    neg_items = [i for i in items if i["sentiment"]["label"] == "消极"]
    if neg_items:
        report += f"\n## 📋 消极舆情样本（前5条）\n\n"
        for item in neg_items[:5]:
            report += f"- [{item['source']}] {item['title']}（得分: {item['sentiment']['score']}）\n"

    report += "\n---\n*本报告由舆情监测 Agent 自动生成*\n"

    output_path = os.path.join(BASE_DIR, f"report_{datetime.now().strftime('%Y%m%d')}.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  报告已保存: {output_path}")
    return output_path


# ============================================================
#  主入口
# ============================================================

def main():
    print("=" * 50)
    print("  舆情监测与热点分析 Agent — Demo")
    print("=" * 50)

    items = load_data()
    items = run_sentiment(items)
    hotspots, events = detect_hotspots(items)
    attr_stats = detect_sensitive_attrs(items)
    report_path = generate_report(items, hotspots, events, attr_stats)

    print(f"\n{'='*50}")
    print(f"  [OK] 全流程跑通")
    print(f"  数据: {len(items)} 条 | 热点词: {len(hotspots)} | 事件: {len(events)}")
    print(f"  报告: {report_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
