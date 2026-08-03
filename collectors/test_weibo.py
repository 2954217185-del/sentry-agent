"""
微博热搜采集测试
用法：
  python test_weibo.py          → 方式1：免费代理API（推荐先试）
  python test_weibo.py cookie   → 方式2：你自己填了Cookie后跑

先确保装好了 requests：
  pip install requests
"""

import requests
import json
import sys
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "test_weibo_hot.json")
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}


# ============================================================
#  方式1：免费代理 API（不需要 Cookie，最简单）
# ============================================================

def test_proxy_api():
    """使用第三方免费聚合 API 抓微博热搜"""
    print("=" * 50)
    print("  方式1：免费代理 API")
    print("=" * 50)
    print()
    print("[请求] https://tenapi.cn/v2/weibohot")
    print()

    try:
        resp = requests.get("https://tenapi.cn/v2/weibohot", headers=HEADERS, timeout=10)
        print(f"[状态码] {resp.status_code}")

        if resp.status_code != 200:
            print(f"[失败] HTTP {resp.status_code}")
            print("[返回内容]", resp.text[:200])
            return

        data = resp.json()
        items = data.get("data", [])

        if not items:
            print("[失败] 返回了 200 但 data 为空，可能 API 改了")
            print("[返回全文]", json.dumps(data, ensure_ascii=False)[:500])
            return

        print(f"[成功] 拿到 {len(items)} 条热搜")
        print()
        print("Top 10 热搜:")
        for i, item in enumerate(items[:10], 1):
            print(f"  {i:>2}. {item.get('name', '')}")

        # 存文件
        result = [{"title": it["name"], "source": "微博热搜", "count": it.get("hot", "")}
                  for it in items[:50]]
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[已保存] {OUTPUT} ({len(result)} 条)")
        return True

    except requests.exceptions.Timeout:
        print("[超时] 网络不通或 API 挂了")
    except requests.exceptions.ConnectionError:
        print("[连接失败] 检查网络")
    except Exception as e:
        print(f"[异常] {e}")
    return False


# ============================================================
#  方式2：直连微博（需要 Cookie）
# ============================================================

def test_direct_cookie():
    """直连微博 API，需要自己填 Cookie"""
    cookie = input("请输入浏览器复制的 Cookie（直接回车跳过）: ").strip()

    if not cookie:
        print("未提供 Cookie，跳过直连测试。")
        print("获取方法: 浏览器登录 weibo.com → F12 → Application → Cookies →")
        print("  复制 SUB 和 SUBP 两个值，用分号拼起来，例如:")
        print("  SUB=_abc123; SUBP=_def456;")
        return False

    headers = {**HEADERS, "Cookie": cookie, "Referer": "https://weibo.com/"}
    url = "https://weibo.com/ajax/side/hotSearch"

    print()
    print("=" * 50)
    print("  方式2：直连微博 API（Cookie 方式）")
    print("=" * 50)
    print()
    print(f"[请求] {url}")

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"[状态码] {resp.status_code}")

        if resp.status_code == 403:
            print("[失败] 403 Forbidden — Cookie 过期或无效，请重新从浏览器获取")
            return False
        elif resp.status_code != 200:
            print(f"[失败] HTTP {resp.status_code}: {resp.text[:200]}")
            return False

        data = resp.json()
        realtime = data.get("data", {}).get("realtime", [])
        if not realtime:
            print("[失败] 拿到 200 但 realtime 为空")
            return False

        print(f"[成功] 拿到 {len(realtime)} 条热搜")
        print()
        print("Top 10:")
        for i, item in enumerate(realtime[:10], 1):
            print(f"  {i:>2}. {item.get('word', '')}  (热度: {item.get('num', '')})")

        result = [{"title": i["word"], "source": "微博热搜",
                    "count": i.get("num", ""), "url": f"https://s.weibo.com/weibo?q={i['word']}"}
                  for i in realtime[:50]]
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n[已保存] {OUTPUT} ({len(result)} 条)")
        return True

    except Exception as e:
        print(f"[异常] {e}")
    return False


# ============================================================
#  主入口
# ============================================================

if __name__ == "__main__":
    print()
    print("  ▎微博热搜采集测试")
    print(f"  ▎保存位置: {OUTPUT}")
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "cookie":
        success = test_direct_cookie()
        if not success:
            print("\n[切换] 试试方式1（免费代理API）...")
            test_proxy_api()
    else:
        success = test_proxy_api()
        if not success:
            print("\n[切换] 试试方式2（需要Cookie）: python test_weibo.py cookie")
