"""
Sentry · 舆情监测智能平台
app.py —— 纯 UI 层，所有逻辑在 modules/ 下
"""
import streamlit as st
import json, os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter

# ---- 导入所有功能模块 ----
from modules.collector import collect_all, load_local, save_local, ALL_SOURCES
from modules.sentiment import batch_analyze, analyze as analyze_sentiment
from modules.hotspot import detect as detect_hotspots, predict_top_keywords
from modules.fairness import detect_attrs, fairness_table
from modules.report import generate as generate_report

# ---- 页面配置 ----
st.set_page_config(page_title="Sentry · 舆情监测", page_icon="", layout="wide")

# ---- 暗夜模式 CSS ----
st.markdown("""<style>
* { font-family: -apple-system, BlinkMacSystemFont, "Microsoft YaHei", "PingFang SC", sans-serif; }
[data-testid="stAppViewContainer"] { background: #0f1117; }
[data-testid="stHeader"] { background: transparent; }
section.main { background: #0f1117; }
.stMarkdown p, .stMarkdown li { color: #b0b5c6 !important; }
h1, h2, h3, h4, h5 { color: #e0e2ea !important; }
[data-testid="stSidebar"] { background: #0d0e15 !important; }
[data-testid="stSidebar"] * { color: #8b8fa3 !important; }
[data-testid="stSidebar"] button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; border: none !important; color: white !important; border-radius: 10px !important; }
[data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] > div { background: #1a1d2e !important; border-color: #2d3148 !important; color: #d0d3e0 !important; }
div[data-testid="stButton"] > button { background: #6366f1; color: white; border: none; border-radius: 10px; font-weight: 500; }
[data-baseweb="select"] > div, [data-baseweb="input"], [data-testid="stNumberInput"] input { background: #1a1d2e !important; border-color: #2d3148 !important; color: #d0d3e0 !important; }
.stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #1e2030; }
.stTabs [data-baseweb="tab"] { padding: 12px 24px; font-weight: 500; color: #6b7280; background: transparent; }
.stTabs [aria-selected="true"] { color: #818cf8 !important; border-bottom: 3px solid #818cf8 !important; }
[data-testid="stDataFrame"] { border: 1px solid #1e2030 !important; }
[data-testid="stDataFrame"] th { background: #1a1d2e !important; color: #8b8fa3 !important; }
[data-testid="stDataFrame"] td { background: #14161f !important; color: #d0d3e0 !important; }
[data-testid="stExpander"], [data-testid="stAlert"] { background: #14161f !important; border-color: #1e2030 !important; }
[data-testid="stMetric"] label, .stCaption { color: #8b8fa3 !important; }
[data-testid="stMetricValue"] { color: #e0e2ea !important; }
[data-testid="stDownloadButton"] > button { background: #6366f1 !important; color: white !important; }
[data-testid="stCheckbox"] label { color: #b0b5c6 !important; }
</style>""", unsafe_allow_html=True)

# ---- Session ----
DEFAULT_SRC = list(ALL_SOURCES.keys())
for k, v in {"data":[], "hotspots":[], "events":[], "attr_stats":{},"fetch_sources":DEFAULT_SRC,"fetch_count":50,"ready":False}.items():
    if k not in st.session_state: st.session_state[k] = v

# ============================================================
#  SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown('<div style="font-size:20px;font-weight:700;color:white;margin-bottom:16px;">Sentry</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#8890a4;letter-spacing:1px;margin-bottom:8px;">数据采集源</p>', unsafe_allow_html=True)
    srcs = []
    for s in ALL_SOURCES:
        if st.checkbox(s, value=s in st.session_state.fetch_sources, key=f"src_{s}"): srcs.append(s)
    st.session_state.fetch_sources = srcs
    n = st.number_input("每个来源采集条数", 10, 100, st.session_state.fetch_count, 10)
    do_fetch = st.button("开始采集数据", use_container_width=True)

    st.markdown('<div style="height:1px;background:#2d3148;margin:20px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:#8890a4;letter-spacing:1px;margin-bottom:8px;">离线数据</p>', unsafe_allow_html=True)
    if st.button("加载本地数据 (raw.json)", use_container_width=True):
        d = load_local()
        if d: st.session_state.data = d; st.session_state.ready = True; st.rerun()
        else: st.warning("raw.json 不存在")
    if st.button("生成模拟数据", use_container_width=True):
        from demo.demo import generate_mock_data
        st.session_state.data = generate_mock_data()
        st.session_state.ready = True; st.rerun()
    st.markdown('<div style="height:1px;background:#2d3148;margin:20px 0;"></div>', unsafe_allow_html=True)
    st.caption("课题 41 · 暑期实训大作业")

# ============================================================
#  FETCH
# ============================================================

if do_fetch:
    with st.spinner("采集中..."):
        items = collect_all(sources=srcs, count=n)
    if items:
        st.session_state.data = items; save_local(items)
        st.session_state.ready = True; st.rerun()
    else: st.sidebar.error("全部采集失败")

# ============================================================
#  WELCOME
# ============================================================

if not st.session_state.ready:
    st.markdown('<div style="text-align:center;padding-top:25vh;"><div style="font-size:48px;"></div><div style="font-size:22px;font-weight:600;color:#e0e2ea;">欢迎使用 Sentry</div><div style="color:#6b7280;margin-top:8px;">在左侧选择采集源并点击「开始采集数据」</div></div>', unsafe_allow_html=True)
    st.stop()

# ============================================================
#  LOAD + ANALYZE
# ============================================================

@st.cache_data(ttl=600, show_spinner="分析中...")
def cached_analysis(data_json):
    try:
        items = json.loads(data_json)
        items = batch_analyze(items)
        hotspots, events = detect_hotspots(items)
        attr_stats = detect_attrs(items)
        predictions = predict_top_keywords(hotspots)
        return items, hotspots, events, attr_stats, predictions
    except Exception as e:
        st.error(f"分析失败: {e}")
        return json.loads(data_json), [], [], {}, []

try:
    data, hotspots, events, attr_stats, predictions = cached_analysis(json.dumps(st.session_state.data, ensure_ascii=False))
except Exception as e:
    st.warning(f"数据加载中，请稍候再试... ({e})")
    st.stop()
total = len(data)
sl = Counter(i["sentiment"]["label"] for i in data)
srcs_count = Counter(i["source"] for i in data)

# ============================================================
#  HEADER
# ============================================================

st.markdown(f'<div style="font-size:26px;font-weight:700;color:#e0e2ea;margin-bottom:4px;">舆情监测分析</div><div style="color:#6b7280;font-size:13px;margin-bottom:24px;">{datetime.now().strftime("%Y-%m-%d %H:%M")} · {total} 条 · {len(srcs_count)} 个来源</div>', unsafe_allow_html=True)

colors_kpi = {"总数":"#6366f1","积极":"#10b981","中性":"#8b8fa3","消极":"#ef4444","热点事件":"#f59e0b"}
metrics = [("总数",total),("积极",sl.get("积极",0)),("中性",sl.get("中性",0)),("消极",sl.get("消极",0)),("热点事件",len(events))]
cols = st.columns(5)
for col,(label,val) in zip(cols, metrics):
    with col:
        st.markdown(f'<div style="background:#14161f;border-radius:14px;padding:18px 20px;border:1px solid #1e2030;"><div style="font-size:12px;color:#8b8fa3;margin-bottom:4px;">{label}</div><div style="font-size:30px;font-weight:700;color:{colors_kpi[label]};">{val}</div></div>', unsafe_allow_html=True)

neg_ratio = sl.get("消极",0)/total if total>0 else 0
if neg_ratio > 0.3:
    st.markdown(f'<div style="background:#2d1b1b;border-left:4px solid #ef4444;padding:14px 18px;border-radius:10px;margin:16px 0;color:#fca5a5;">消极情绪 {neg_ratio*100:.1f}%，超 30% 警戒线</div>', unsafe_allow_html=True)

# ============================================================
#  TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(["数据总览", "热点洞察", "公平性分析", "舆情检索", "导出报告"])

# --- Tab 1 ---
with tab1:
    c1, c2 = st.columns(2)
    with c1:
        fig1 = go.Figure(go.Pie(labels=["积极","中性","消极"], values=[sl.get("积极",0),sl.get("中性",0),sl.get("消极",0)], hole=0.65, marker_colors=["#10b981","#8b8fa3","#ef4444"], textinfo='percent', sort=False))
        fig1.update_layout(margin=dict(l=0,r=0,t=10,b=10), height=300, paper_bgcolor="#14161f", plot_bgcolor="#14161f", legend=dict(orientation="h",y=-0.1), annotations=[dict(text=f"<b>{total}</b>",x=0.5,y=0.5,font_size=24,showarrow=False)], font_color="#b0b5c6")
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
    with c2:
        names = list(srcs_count.keys()); vals = list(srcs_count.values())
        fig2 = go.Figure(go.Bar(x=vals, y=names, orientation='h', marker_color="#6366f1", marker_cornerradius=6, text=vals, textposition="outside"))
        fig2.update_layout(margin=dict(l=0,r=40,t=10,b=10), height=300, paper_bgcolor="#14161f", plot_bgcolor="#14161f", xaxis_visible=False, font_color="#b0b5c6")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    rows = []
    for s in names:
        si = [i for i in data if i["source"]==s]
        if si:
            sc = Counter(i["sentiment"]["label"] for i in si)
            rows.append({"来源":s,"数量":len(si),"积极":sc.get("积极",0),"中性":sc.get("中性",0),"消极":sc.get("消极",0),"正面率":f"{sc.get('积极',0)/len(si)*100:.0f}%"})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, column_config={"正面率": st.column_config.ProgressColumn("正面率",min_value=0,max_value=100,format="%s")})

# --- Tab 2 ---
with tab2:
    c1, c2 = st.columns([1, 1.4])
    with c1:
        kw_names = [h["keyword"] for h in hotspots[:10]][::-1]
        kw_vals = [h["count"] for h in hotspots[:10]][::-1]
        fig3 = go.Figure(go.Bar(x=kw_vals, y=kw_names, orientation='h', marker_color="#6366f1", marker_cornerradius=6, text=kw_vals, textposition="outside"))
        fig3.update_layout(margin=dict(l=0,r=40,t=10,b=10), height=350, paper_bgcolor="#14161f", plot_bgcolor="#14161f", xaxis_visible=False, font_color="#b0b5c6")
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    with c2:
        for e in events:
            st.markdown(f'<div style="background:#14161f;border-radius:10px;padding:14px 16px;border:1px solid #1e2030;margin-bottom:10px;"><div style="font-weight:600;color:#e0e2ea;">{e["name"]}</div><div style="font-size:12px;color:#6b7280;margin:4px 0 8px;">共现 {e["co_occur"]} 次</div>{"".join(f"<div style=\"font-size:12px;color:#8b8fa3;\">- {a[:60]}</div>" for a in e["articles"][:3])}</div>', unsafe_allow_html=True)

    if predictions:
        st.markdown('<p style="font-size:15px;font-weight:600;color:#e0e2ea;margin:16px 0 8px;">热度预测</p>', unsafe_allow_html=True)
        pd_rows = [{"关键词":p["keyword"],"当前热度":p["current"],"明日预测":p["pred_1d"],"7日预测":p["pred_7d"],"趋势":p["trend"]} for p in predictions]
        st.dataframe(pd.DataFrame(pd_rows), use_container_width=True, hide_index=True)

# --- Tab 3 ---
with tab3:
    if attr_stats:
        cols = st.columns(len(attr_stats))
        for idx, (cat, info) in enumerate(attr_stats.items()):
            with cols[idx]:
                st.markdown(f'<div style="background:#14161f;border-radius:12px;padding:16px;border:1px solid #1e2030;text-align:center;"><div style="font-size:12px;color:#8b8fa3;">{cat}</div><div style="font-size:28px;font-weight:700;color:#6366f1;">{info["total"]}</div><div style="font-size:11px;color:#6b7280;margin-top:4px;">{", ".join(f"{k}({v})" for k,v in info["top"][:3])}</div></div>', unsafe_allow_html=True)

    ft = fairness_table(data, attr_stats)
    if ft:
        st.dataframe(pd.DataFrame(ft), use_container_width=True, hide_index=True)

# --- Tab 4 ---
with tab4:
    sf = []; c1,c2,_ = st.columns([1,1,2])
    for s in srcs_count: 
        if c1.checkbox(s, value=True, key=f"ft_{s}"): sf.append(s)
    ef = []
    for e in ["积极","中性","消极"]:
        if c2.checkbox(e, value=True, key=f"fe_{e}"): ef.append(e)
    kw = st.text_input("关键词搜索", placeholder="输入关键词...")
    filtered = [it for it in data if it["source"] in sf and it["sentiment"]["label"] in ef and (not kw or kw in it["title"])]
    td = []
    for it in filtered[:100]:
        e = "🟢" if it["sentiment"]["label"]=="积极" else "🟡" if it["sentiment"]["label"]=="中性" else "🔴"
        td.append({"":e,"标题":it["title"],"来源":it["source"],"得分":it["sentiment"]["score"],"时间":it.get("time","")})
    st.dataframe(pd.DataFrame(td), use_container_width=True, hide_index=True, column_config={"得分": st.column_config.ProgressColumn("得分",min_value=-1,max_value=1,format="%.2f")})

# --- Tab 5 ---
with tab5:
    rp, rm = generate_report(data, hotspots, events, attr_stats)
    with st.expander("预览日报", expanded=True): st.markdown(rm)
    st.download_button("下载报告", rm, file_name=f"report_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown", use_container_width=True)

# ============================================================
#  FOOTER
# ============================================================

st.markdown('<div style="margin-top:40px;padding-top:20px;border-top:1px solid #1e2030;display:flex;justify-content:space-between;color:#6b7280;font-size:12px;"><span>Sentry · 舆情监测与热点分析智能平台</span><span>课题 41 · 暑期实训大作业</span></div>', unsafe_allow_html=True)
