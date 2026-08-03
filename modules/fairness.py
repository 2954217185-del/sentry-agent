"""
modules/fairness.py —— 敏感属性检测 + 公平性分析
"""

from collections import Counter, defaultdict

SENSITIVE = {
    "性别": ["女子","男子","女性","男性","女司机","男司机","女教师","女孩","男孩","妇女","性别"],
    "地域": ["北京","上海","广州","深圳","河南","山东","东北","南方","北方","农村","城市","乡镇"],
    "年龄": ["年轻人","老年人","老人","00后","90后","80后","大学生","中学生","小学生","儿童","少年","中年","青年","30岁"],
    "职业": ["外卖员","快递员","程序员","工人","教师","医生","护士","警察","公务员","农民工","学生","主播","网红","明星"],
    "身份": ["穷人","富人","底层","精英","体制内","海归","本地人","外地人","租客","残疾人","单亲","留守","孕妇","家长"],
}


def detect_attrs(items):
    """
    检测每条数据的敏感属性
    返回: {
        "类别名": {
            "total": int,            # 总提及次数
            "top": [("词", 次数), ...]  # Top 3
        }, ...
    }
    """
    ac = defaultdict(Counter)
    for it in items:
        for cat, pats in SENSITIVE.items():
            for p in pats:
                if p in it["title"]:
                    ac[cat][p] += 1
    stats = {}
    for cat, c in ac.items():
        stats[cat] = {"total": sum(c.values()), "top": c.most_common(3)}
    return stats


def fairness_table(items, attr_stats):
    """
    生成公平性表格
    返回: [{"类别": str, "群体": str, "提及": int, "正面率": str, "负面率": str}, ...]
    """
    rows = []
    for cat, info in attr_stats.items():
        for kw, cnt in info["top"][:5]:
            kw_items = [it for it in items if kw in it["title"]]
            if kw_items:
                ks = Counter(it["sentiment"]["label"] for it in kw_items)
                n = len(kw_items)
                rows.append({
                    "类别": cat, "群体": kw, "提及": cnt,
                    "正面率": f"{ks.get('积极',0)/n*100:.0f}%",
                    "负面率": f"{ks.get('消极',0)/n*100:.0f}%"
                })
    return rows
