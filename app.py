"""
Sentry — 舆情监测智能平台
"""
import streamlit as st
import json, os, re, requests
import pandas as pd
# plotly 有 numpy 2.0 兼容问题，用 Streamlit 原生图表
from datetime import datetime
from collections import Counter, defaultdict

st.set_page_config(page_title="Sentry · 舆情监测", page_icon="", layout="wide")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "collectors", "data")
os.makedirs(DATA_DIR, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

# ============================================================
#  CSS
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

/* root */
[data-testid="stAppViewContainer"] { background: #f0f2f6; }
[data-testid="stHeader"] { background: transparent; }

/* sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1d2e 0%, #252840 100%); }
[data-testid="stSidebar"] * { color: #d0d3e0 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: white !important; }
[data-testid="stSidebar"] button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important; color: white !important; border-radius: 10px !important;
    font-weight: 500 !important; transition: 0.2s !important;
}
[data-testid="stSidebar"] button:hover { opacity: 0.9; transform: translateY(-1px); }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #2d3148 !important; border: 1px solid #3d4260 !important; }
[data-testid="stSidebar"] input { background: #2d3148 !important; border: 1px solid #3d4260 !important; color: white !important; }
[data-testid="stSidebar"] [data-testid="stMarkdown"] p { color: #8890a4 !important; }

/* sidebar multiselect tags */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background: #4338ca !important; color: white !important;
    border-radius: 6px !important; font-weight: 500 !important;
    font-size: 12px !important; padding: 2px 8px !important;
    height: auto !important; line-height: 1.4 !important;
    white-space: nowrap !important; overflow: visible !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] span {
    overflow: visible !important; text-overflow: clip !important;
    max-width: none !important;
}

/* fix white-on-white buttons in main area */
div[data-testid="stButton"] > button {
    border-radius: 10px; font-weight: 500; transition: 0.2s;
    background: #6366f1; color: white; border: none;
}
div[data-testid="stButton"] > button:hover { background: #4f46e5; }

/* fix multiselect/input in main area */
[data-baseweb="select"] > div { border-color: #d0d5dd !important; }
[data-baseweb="input"] { border-color: #d0d5dd !important; }

/* block container cards */
[data-testid="stVerticalBlock"] > div[style*="flex-direction: column"] > div {
    background: white; border-radius: 14px;
    padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
    border: 1px solid #e8ecf1; margin-bottom: 16px;
}
[data-testid="stSidebar"] button:hover { opacity: 0.9; transform: translateY(-1px); }
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #2d3148 !important; border: 1px solid #3d4260 !important; }
[data-testid="stSidebar"] input { background: #2d3148 !important; border: 1px solid #3d4260 !important; color: white !important; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 2px solid #e8ecf1; }
.stTabs [data-baseweb="tab"] {
    border-radius: 0; padding: 12px 24px; font-weight: 500; color: #8890a4;
    background: transparent; border: none; transition: 0.2s;
}
.stTabs [aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom: 3px solid #6366f1 !important; margin-bottom: -2px;
    font-weight: 600;
}

/* buttons */
div[data-testid="stButton"] > button {
    border-radius: 10px; font-weight: 500; transition: 0.2s;
}

/* dataframe */
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid #e8ecf1; }
[data-testid="stDataFrame"] th { background: #f8f9fb !important; font-weight: 600 !important; color: #4a4f5c !important; }

/* expander */
[data-testid="stExpander"] { border: 1px solid #e8ecf1 !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  工具
# ============================================================

STOPWORDS = {"的","了","是","在","和","也","都","就","不","与","及","从","对","以","到",
    "但","而","或","等","这","那","上","下","中","有","人","大","个","一","会","可",
    "着","过","还","吗","啊","吧","呢","哦","如何","怎样","可以","应该","能够","已经",
    "因为","所以","但是","如果","没有","不是","这个","那个","什么","为什么"}

POSITIVE = {"好","赞","优秀","厉害","支持","爱","喜欢","期待","成功","突破","创新",
    "进步","希望","加油","祝贺","恭喜","美丽","精彩","太棒","给力","绝了","宝藏","治愈",
    "温暖","感动","造福","安全","高效","便捷","公平","正义","良心","实惠","开放","透明",
    "利好","友好","和谐","稳定","合理","重磅","惊艳","完美","封神","第一","顶","里程碑",
    "好消息","优惠","免费","福利","惠及","冠军","金牌","获奖","好评","表扬","表彰",
    "就业","减税","补贴","改善","恢复","起飞","爆发","太强了","拍手称快","稳中向好",
    "飞跃","新纪录","实至名归","大快人心","看好","点赞","省心","舒心","给力"}

NEGATIVE = {"差","烂","垃圾","失望","失败","抗议","投诉","黑幕","腐败","不公","歧视",
    "造假","欺骗","隐瞒","泄露","暴力","事故","灾难","死亡","坍塌","爆炸","火灾","地震",
    "洪水","倒闭","破产","裁员","失业","涨价","下跌","暴跌","亏损","违规","罚款","处罚",
    "判刑","停职","下台","撤职","崩了","翻车","塌房","恶心","无耻","抹黑","造谣","谣言",
    "陷阱","坑","焦虑","恐慌","担忧","危机","威胁","风险","隐患","漏洞","脏","乱",
    "抵制","封杀","限制","禁止","致癌","有毒","污染","超标","变质","受害","牺牲","伤亡",
    "失踪","失联","致命","丢人","怒怼","买不起","太丢人","吓人","可怕","坑人"}

DEG = {"非常":2.0,"十分":2.0,"特别":2.0,"极其":2.5,"太":1.8,"很":1.5,"真":1.5,"挺":1.2,"有点":0.6,"相当":1.6}
NEGATION = {"不","没","无","非","未","别","莫","勿","否"}

SENSITIVE = {
    "性别":["女子","男子","女性","男性","女司机","男司机","女教师","女孩","男孩","妇女","性别"],
    "地域":["北京","上海","广州","深圳","河南","山东","东北","南方","北方","农村","城市","乡镇"],
    "年龄":["年轻人","老年人","老人","00后","90后","80后","大学生","中学生","小学生","儿童","少年","中年","青年","30岁"],
    "职业":["外卖员","快递员","程序员","工人","教师","医生","护士","警察","公务员","农民工","学生","主播","网红","明星"],
    "身份":["穷人","富人","底层","精英","体制内","海归","本地人","外地人","租客","残疾人","单亲","留守","孕妇","家长"]}


def tokenize(text):
    s = re.sub(r'[，。！？；：、\s,.!?;:()\[\]]+', ' ', text)
    words = []
    for seg in s.split():
        for n in (4, 3, 2):
            for i in range(len(seg) - n + 1):
                w = seg[i:i+n]
                if re.search(r'[\u4e00-\u9fff]', w): words.append(w)
    return words


# ============================================================
#  采集器
# ============================================================

def fetch_toutiao(n):
    try: r=requests.get("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("Title","").strip(),"source":"今日头条","url":i.get("Url",""),"time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for i in r.json().get("data",[]) if i.get("Title","").strip()][:n]

def fetch_baidu(n):
    try: r=requests.get("https://top.baidu.com/board?tab=realtime",headers=HEADERS,timeout=8)
    except: return []
    titles=re.findall(r'<div[^>]*class="c-single-text-ellipsis"[^>]*>(.+?)</div>',r.text,re.DOTALL)
    return [{"title":t.strip(),"source":"百度热搜","url":"","time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for t in titles[:n] if t.strip()]

def fetch_thepaper(n):
    try: r=requests.get("https://cache.thepaper.cn/contentapi/wwwIndex/rightSidebar",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("name","").strip(),"source":"澎湃新闻","url":"","time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for i in r.json().get("data",{}).get("hotNews",[]) if i.get("name","").strip()][:n]

def fetch_weibo(n):
    try: r=requests.get("https://api.qqsuu.cn/api/dm-weibohot",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("hotword","").strip(),"source":"微博热搜","url":"","time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for i in r.json().get("data",{}).get("list",[]) if i.get("hotword","").strip()][:n]

def fetch_cctv(n):
    try: r=requests.get("https://news.cctv.com/2019/07/gaiban/cmsdatainterface/page/news_1.jsonp",headers=HEADERS,timeout=8)
    except: return []
    m=re.search(r"\(({.*})\)",r.text,re.DOTALL)
    if not m: return []
    return [{"title":i.get("title","").strip(),"source":"央视新闻","url":i.get("url",""),"time":i.get("focus_date",""),"summary":i.get("brief","")[:200]} for i in json.loads(m.group(1)).get("data",{}).get("list",[]) if i.get("title","").strip()][:n]

def fetch_baidu_news(n):
    try:
        items=[]
        for kw in ["社会","民生","教育","科技"][:3]:
            r=requests.get(f"https://news.baidu.com/ns?word={kw}&pn=0&rn=20",headers=HEADERS,timeout=8)
            titles=re.findall(r'<h3[^>]*class="news-title[^"]*"[^>]*>\s*<a[^>]*>(.*?)</a>',r.text,re.DOTALL)
            abs_=re.findall(r'<div[^>]*class="c-abstract"[^>]*>(.*?)</div>',r.text,re.DOTALL)
            for i,t in enumerate([re.sub(r'<[^>]+>','',t).strip() for t in titles]):
                if t:
                    item={"title":t,"source":"百度新闻","url":"","time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    if i<len(abs_): item["summary"]=re.sub(r'<[^>]+>','',abs_[i]).strip()[:200]
                    items.append(item)
            if len(items)>=n: break
        return items[:n]
    except: return []

def fetch_bilibili(n):
    try: r=requests.get("https://api.bilibili.com/x/web-interface/popular?ps=50",headers={**HEADERS,"Referer":"https://www.bilibili.com/"},timeout=8)
    except: return []
    return [{"title":v.get("title","").strip(),"source":"B站热门","url":f"https://www.bilibili.com/video/{v.get('bvid','')}","time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for v in r.json().get("data",{}).get("list",[]) if v.get("title","").strip()][:n]

def fetch_sina(n):
    try: r=requests.get("https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2509&num=50",headers=HEADERS,timeout=8)
    except: return []
    return [{"title":i.get("title","").strip(),"source":"新浪新闻","url":i.get("url",""),"time":i.get("ctime",""),"summary":i.get("intro","")[:200]} for i in r.json().get("result",{}).get("data",[]) if i.get("title","").strip()][:n]

COLLECTORS = {"今日头条":fetch_toutiao,"百度热搜":fetch_baidu,"澎湃新闻":fetch_thepaper,"微博热搜":fetch_weibo,"央视新闻":fetch_cctv,"百度新闻":fetch_baidu_news,"B站热门":fetch_bilibili,"新浪新闻":fetch_sina}

# ============================================================
#  分析
# ============================================================

@st.cache_data(ttl=600, show_spinner="正在分析数据...")
def run_analysis(raw_json):
    raw=json.loads(raw_json)
    for it in raw:
        pos=sum(1 for w in POSITIVE if w in it["title"])
        neg=sum(1 for w in NEGATIVE if w in it["title"])
        for d,m in DEG.items():
            for pw in POSITIVE:
                if d+pw in it["title"]: pos+=0.5*m
            for nw in NEGATIVE:
                if d+nw in it["title"]: neg+=0.5*m
        for nw in NEGATION:
            for pw in POSITIVE:
                if nw+pw in it["title"]: pos-=1; neg+=0.5
        tot=max(pos+neg,0.01); s=max(-1.,min(1.,(pos-neg)/tot))
        it["sentiment"]={"score":round(s,3),"label":"积极" if s>0.08 else "消极" if s<-0.08 else "中性"}
    wc=Counter()
    for it in raw:
        for w in tokenize(it["title"]):
            if w not in STOPWORDS and len(w)>=2: wc[w]+=1
    top=wc.most_common(15)
    hotspots=[{"keyword":w,"count":c} for w,c in top]
    events=[]
    used=set()
    for w1,_ in top[:10]:
        for w2,_ in top[:10]:
            if w1>=w2: continue
            cnt=sum(1 for it in raw if w1 in it["title"] and w2 in it["title"])
            if cnt>=3 and w1 not in used and w2 not in used:
                used.update([w1,w2])
                events.append({"name":f"{w1}+{w2}","co_occur":cnt,"articles":[it["title"] for it in raw if w1 in it["title"] and w2 in it["title"]][:3]})
    ac=defaultdict(Counter)
    for it in raw:
        for cat,pats in SENSITIVE.items():
            for p in pats:
                if p in it["title"]: ac[cat][p]+=1
    attr_stats={}
    for cat,c in ac.items():
        t=sum(c.values()); attr_stats[cat]={"total":t,"top":c.most_common(3)}
    return raw,hotspots,events,attr_stats

# ============================================================
#  Session
# ============================================================

DEFAULT_SOURCES = ["今日头条","百度热搜","澎湃新闻","微博热搜","央视新闻","百度新闻","B站热门","新浪新闻"]
for k,v in {"data":[],"hotspots":[],"events":[],"attr_stats":{},"fetch_sources":DEFAULT_SOURCES,"fetch_count":20,"ready":False}.items():
    if k not in st.session_state: st.session_state[k]=v

# ============================================================
#  Sidebar
# ============================================================

with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:24px;">
        <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;color:white;"></div>
        <div>
            <div style="font-size:18px;font-weight:700;color:white !important;">Sentry</div>
            <div style="font-size:11px;color:#8890a4;">舆情监测平台</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;color:#8890a4;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">数据采集源</p>',unsafe_allow_html=True)
    srcs = st.multiselect("", list(COLLECTORS.keys()), default=st.session_state.fetch_sources, label_visibility="collapsed")
    n = st.number_input("每个来源采集条数", 10, 50, st.session_state.fetch_count, 10)
    do_fetch = st.button("开始采集数据", use_container_width=True)

    st.markdown('<div style="height:1px;background:#2d3148;margin:20px 0;"></div>', unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;color:#8890a4;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">离线数据</p>',unsafe_allow_html=True)
    if st.button("加载本地数据 (raw.json)", use_container_width=True):
        p=os.path.join(DATA_DIR,"raw.json")
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: st.session_state.data=json.load(f)
            st.session_state.ready=True; st.rerun()
        else: st.warning("raw.json 不存在")
    if st.button("生成模拟数据", use_container_width=True):
        from demo.demo import generate_mock_data
        st.session_state.data=generate_mock_data()
        st.session_state.ready=True; st.rerun()

    st.markdown('<div style="height:1px;background:#2d3148;margin:20px 0;"></div>', unsafe_allow_html=True)
    st.caption("课题 41 · 暑期实训大作业")

# ============================================================
#  Collect
# ============================================================

if do_fetch:
    all_items=[]
    for s in srcs:
        f=COLLECTORS.get(s)
        if f:
            items=f(n)
            all_items.extend(items)
            if items: st.sidebar.success(f"{s}: {len(items)} 条")
            else: st.sidebar.warning(f"{s}: 失败")
    if all_items:
        st.session_state.data=all_items
        with open(os.path.join(DATA_DIR,"raw.json"),"w",encoding="utf-8") as fh: json.dump(all_items,fh,ensure_ascii=False,indent=2)
        st.session_state.ready=True; st.rerun()
    else: st.sidebar.error("全部采集失败")

# ============================================================
#  Analysis
# ============================================================

if not st.session_state.ready:
    st.markdown("""
    <div style="display:flex;align-items:center;justify-content:center;height:60vh;flex-direction:column;gap:16px;">
        <div style="font-size:48px;"></div>
        <div style="font-size:22px;font-weight:600;color:#1a1d2e;">欢迎使用 Sentry</div>
        <div style="color:#8890a4;font-size:14px;">请在左侧选择采集源并点击「开始采集数据」</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

data, hotspots, events, attr_stats = run_analysis(json.dumps(st.session_state.data, ensure_ascii=False))
total=len(data)
sl=Counter(i["sentiment"]["label"] for i in data)
srcs_count=Counter(i["source"] for i in data)

# ============================================================
#  Header
# ============================================================

c_title, c_report = st.columns([4, 1])
with c_title:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
        <div style="font-size:26px;font-weight:700;color:#1a1d2e;">舆情监测分析</div>
        <div style="font-size:12px;color:#8890a4;background:#eef0f5;padding:3px 10px;border-radius:20px;">{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    <div style="color:#8890a4;font-size:13px;margin-bottom:24px;">
        {total} 条数据 · {len(srcs_count)} 个来源
    </div>
    """, unsafe_allow_html=True)

# KPI Cards
colors = {"总数":"#6366f1","积极":"#10b981","中性":"#8b8fa3","消极":"#ef4444","热点事件":"#f59e0b"}
metrics_data = [
    ("总数", total),
    ("积极", sl.get("积极",0)),
    ("中性", sl.get("中性",0)),
    ("消极", sl.get("消极",0)),
    ("热点事件", len(events)),
]

kpi_html = '<div style="display:flex;gap:12px;margin-bottom:28px;">'
for label, val in metrics_data:
    kpi_html += f"""
    <div style="flex:1;background:white;border-radius:14px;padding:18px 20px;border:1px solid #eef0f5;box-shadow:0 1px 3px rgba(0,0,0,.02);">
        <div style="font-size:12px;color:#8890a4;font-weight:500;margin-bottom:4px;">{label}</div>
        <div style="font-size:30px;font-weight:700;color:{colors[label]};">{val}</div>
    </div>"""
kpi_html += '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)

neg_ratio = sl.get("消极",0)/total if total>0 else 0
if neg_ratio>0.3:
    st.markdown(f"""
    <div style="background:#fef2f2;border-left:4px solid #ef4444;padding:14px 18px;border-radius:10px;margin-bottom:20px;color:#991b1b;font-weight:500;">
        负面预警：消极情绪占比 {neg_ratio*100:.1f}%，已超过 30% 警戒阈值
    </div>
    """, unsafe_allow_html=True)

# ============================================================
#  Tabs
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(["数据总览", "热点洞察", "公平性分析", "舆情检索", "导出报告"])

# ============================================================
#  Tab 1: Overview
# ============================================================

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:12px;">情感分布</p>', unsafe_allow_html=True)
        df_sent = pd.DataFrame({"类型":["积极","中性","消极"],"数量":[sl.get("积极",0),sl.get("中性",0),sl.get("消极",0)]})
        st.bar_chart(df_sent.set_index("类型"), use_container_width=True)

    with c2:
        st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:12px;">来源分布</p>', unsafe_allow_html=True)
        df_src = pd.DataFrame({"来源":list(srcs_count.keys()),"数量":list(srcs_count.values())})
        st.bar_chart(df_src.set_index("来源"), horizontal=True, use_container_width=True)

# ============================================================
#  Tab 2: Hotspot
# ============================================================

with tab2:
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:12px;">热点关键词 Top 10</p>', unsafe_allow_html=True)
        kw_df = pd.DataFrame({"关键词":[h["keyword"] for h in hotspots[:10]],"热度":[h["count"] for h in hotspots[:10]]})
        st.bar_chart(kw_df.set_index("关键词"), horizontal=True, use_container_width=True)

    with c2:
        st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:12px;">热点事件</p>', unsafe_allow_html=True)
        if events:
            for e in events:
                st.markdown(f"""
                <div style="background:white;border-radius:10px;padding:14px 16px;border:1px solid #eef0f5;margin-bottom:10px;">
                    <div style="font-weight:600;color:#1a1d2e;margin-bottom:6px;">{e['name']}</div>
                    <div style="font-size:12px;color:#8890a4;margin-bottom:8px;">共现 {e['co_occur']} 次</div>
                    {''.join(f'<div style="font-size:12px;color:#6b7280;margin-bottom:2px;">- {a[:60]}</div>' for a in e['articles'][:3])}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("暂未检测到显著热点事件")

    # 词云
    st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:12px;">关键词词云</p>', unsafe_allow_html=True)
    sizes = {h["keyword"]: h["count"] for h in hotspots[:20]}
    mx = max(sizes.values()) if sizes else 1
    html = []
    for w, c in sorted(sizes.items(), key=lambda x:-x[1]):
        fs = max(13, int(13 + c/mx*34))
        op = max(0.35, c/mx)
        html.append(f'<span style="font-size:{fs}px;opacity:{op};padding:3px 6px;display:inline-block;color:#6366f1;font-weight:{600 if c>mx*0.6 else 400}">{w}</span>')
    st.markdown(f'<div style="background:white;border-radius:12px;padding:20px;border:1px solid #eef0f5;line-height:2.4;text-align:center;">{" ".join(html)}</div>', unsafe_allow_html=True)

# ============================================================
#  Tab 3: Fairness
# ============================================================

with tab3:
    st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:16px;">敏感属性分布</p>', unsafe_allow_html=True)
    if attr_stats:
        cols = st.columns(len(attr_stats))
        for idx, (cat, info) in enumerate(attr_stats.items()):
            with cols[idx]:
                st.markdown(f"""
                <div style="background:white;border-radius:12px;padding:16px;border:1px solid #eef0f5;text-align:center;">
                    <div style="font-size:12px;color:#8890a4;margin-bottom:4px;">{cat}</div>
                    <div style="font-size:28px;font-weight:700;color:#6366f1;">{info['total']}</div>
                    <div style="font-size:11px;color:#9ca3af;margin-top:6px;">{', '.join(f'{k}({v})' for k,v in info['top'][:3])}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin:24px 0 12px;">群体公平性一览</p>', unsafe_allow_html=True)
    rows=[]
    for cat,info in attr_stats.items():
        for kw,cnt in info["top"][:5]:
            kw_items=[it for it in data if kw in it["title"]]
            if kw_items:
                ks=Counter(it["sentiment"]["label"] for it in kw_items)
                rows.append({"类别":cat,"群体":kw,"提及":cnt,"正面率":f"{ks.get('积极',0)/len(kw_items)*100:.0f}%","负面率":f"{ks.get('消极',0)/len(kw_items)*100:.0f}%"})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                     column_config={"正面率":st.column_config.ProgressColumn("正面率",min_value=0,max_value=100,format="%s",width="small"),
                                    "负面率":st.column_config.ProgressColumn("负面率",min_value=0,max_value=100,format="%s",width="small")})

# ============================================================
#  Tab 4: Data Table
# ============================================================

with tab4:
    sf = st.multiselect("来源", list(srcs_count.keys()), default=list(srcs_count.keys()), label_visibility="collapsed",
                        placeholder="按来源筛选")
    c_filt = st.columns(3)
    ef = c_filt[0].multiselect("情感", ["积极","中性","消极"], default=["积极","中性","消极"], placeholder="按情感筛选")
    kw = c_filt[1].text_input("", placeholder="搜索关键词...")
    c_filt[2].caption(f'{" "}')

    filtered = [it for it in data if it["source"] in sf and it["sentiment"]["label"] in ef
                and (not kw or kw in it["title"])]

    table_data = []
    for it in filtered[:100]:
        e = "🟢" if it["sentiment"]["label"]=="积极" else "🟡" if it["sentiment"]["label"]=="中性" else "🔴"
        table_data.append({"": e, "标题": it["title"], "来源": it["source"],
                           "得分": it["sentiment"]["score"], "时间": it.get("time","")})
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True,
                 column_config={"": st.column_config.TextColumn("", width="small"),
                                "标题": st.column_config.TextColumn("标题", width="large"),
                                "得分": st.column_config.ProgressColumn("得分", min_value=-1, max_value=1,
                                    format="%.2f", width="small")})

# ============================================================
#  Tab 5: Report
# ============================================================

with tab5:
    st.markdown('<p style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:12px;">舆情日报生成</p>', unsafe_allow_html=True)
    today=datetime.now().strftime("%Y%m%d")
    report = f"# 舆情日报 {datetime.now().strftime('%Y-%m-%d')}\n\n"
    report += f"> {total} 条数据 · {', '.join(srcs_count.keys())}\n\n---\n\n"
    report += "## 情感概览\n|类型|数量|占比|\n|---|---|---|\n"
    for k in ["积极","消极","中性"]: report += f"|{k}|{sl.get(k,0)}|{sl.get(k,0)/total*100:.1f}%|\n"
    report += "\n## 热点关键词 Top 10\n|关键词|热度|\n|---|---|\n"
    for h in hotspots[:10]: report += f"|{h['keyword']}|{h['count']}|\n"
    if events:
        report += f"\n## 热点事件 ({len(events)})\n\n"
        for e in events:
            report += f"### {e['name']}（共现 {e['co_occur']} 次）\n"
            for a in e["articles"]: report += f"- {a}\n"
    report += "\n## 敏感属性\n|类别|提及|Top词汇|\n|---|---|---|\n"
    for cat, info in attr_stats.items():
        report += f"|{cat}|{info['total']}|{', '.join(f'{k}({v})' for k,v in info['top'])}|\n"
    report += "\n---\n*Sentry 舆情监测平台自动生成*"

    c_r1, c_r2 = st.columns([3, 1])
    with c_r1:
        with st.expander("预览报告", expanded=True):
            st.markdown(report)
    with c_r2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("下载 Markdown 报告", report, file_name=f"report_{today}.md",
                           mime="text/markdown", use_container_width=True)

# ============================================================
#  Footer
# ============================================================

st.markdown("""
<div style="margin-top:40px;padding-top:20px;border-top:1px solid #e8ecf1;display:flex;justify-content:space-between;align-items:center;">
    <div style="color:#8890a4;font-size:12px;">Sentry · 舆情监测与热点分析智能平台</div>
    <div style="color:#8890a4;font-size:12px;">课题 41 · 暑期实训大作业</div>
</div>
""", unsafe_allow_html=True)
