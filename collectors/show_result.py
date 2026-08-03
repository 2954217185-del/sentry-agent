import json
with open("test_weibo_hot.json", "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"共 {len(data)} 条")
for d in data[:10]:
    print(f"  {d['title']}  热度:{d['count']}")
