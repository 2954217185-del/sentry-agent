"""微博热搜采集 — 使用 qqsuu 免费API"""
import requests, json

r = requests.get("https://api.qqsuu.cn/api/dm-weibohot",
                 headers={"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}, timeout=10)

print(f"状态码: {r.status_code}")

data = r.json()
items = data["data"]["list"]
print(f"拿到 {len(items)} 条热搜\n")

for i, it in enumerate(items[:15], 1):
    hw = it["hotword"]
    num = it.get("hotwordnum", "").strip()
    print(f"{i:>2}. {hw}  (热度: {num})")

# 保存
result = [{"title": it["hotword"], "source": "微博热搜",
           "count": it.get("hotwordnum", "").strip(),
           "time": __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
          for it in items[:50]]
with open("test_weibo_hot.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\n已保存 {len(result)} 条到 test_weibo_hot.json")
