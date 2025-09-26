# generate_news.py
# 说明：运行后会在 news/ 目录生成两个文件：
#  - news/daily_news_YYYYMMDD.html   （带日期的网页）
#  - news/news_feed.xml              （固定的 RSS 文件，用于 IFTTT 订阅）
#
# 依赖：feedparser （workflow 中已安装）

import feedparser
import datetime
import html
import time

# --- 配置：RSS 源（可按需增删） ---
RSS_FEEDS = [
    ("Reuters", "https://feeds.reuters.com/reuters/worldNews"),
    ("BBC", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("TheGuardian", "https://www.theguardian.com/world/rss"),
    ("FoxNews", "http://feeds.foxnews.com/foxnews/world"),
    ("Independent", "https://www.independent.co.uk/news/world/rss"),
    ("AFP", "https://www.afp.com/en/rss")   # 若不可用可删除
]

# 关键字：用于识别中东/以色列相关条目（优先）
ME_KEYWORDS = ["israel", "gaza", "palestine", "hezbollah", "iran", "middle east", "hamas"]

MAX_ITEMS = 10
MIN_ME_ITEMS = 2  # 至少保留多少条中东相关新闻（如果能找到）

def is_middle_east(item_text):
    t = item_text.lower()
    return any(k in t for k in ME_KEYWORDS)

def safe_get(entry, key):
    return entry.get(key, "") or entry.get("summary", "") or entry.get("description", "")

def to_rfc2822(dt):
    # dt: datetime.datetime
    return dt.strftime("%a, %d %b %Y %H:%M:%S GMT")

def choose_items(collected):
    # collected: list of dicts with keys: title, link, summary, published_dt (datetime or None), source
    # 先选中东相关，再按时间/原始顺序补到 MAX_ITEMS
    me = []
    others = []
    seen = set()
    for it in collected:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        text = (it["title"] + " " + it["summary"]).lower()
        if is_middle_east(text):
            me.append(it)
        else:
            others.append(it)
    # 排序：有 published_dt 的按时间倒序
    def sort_key(x):
        return x["published_dt"] or datetime.datetime.utcnow()
    me.sort(key=sort_key, reverse=True)
    others.sort(key=sort_key, reverse=True)

    result = []
    # 先放中东相关（最多 MIN_ME_ITEMS）
    while me and len(result) < MIN_ME_ITEMS:
        result.append(me.pop(0))
    # 然后依时间顺序合并剩余，直到 MAX_ITEMS
    combined = me + others
    for it in combined:
        if len(result) >= MAX_ITEMS:
            break
        result.append(it)
    # 若不足 MIN_ME_ITEMS，接受现有数量（保证不抛错）
    return result[:MAX_ITEMS]

def main():
    collected = []
    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[WARN] failed parse {url}: {e}")
            continue
        entries = getattr(feed, "entries", []) or []
        # 取每源前 6 条（避免抓太多）
        for entry in entries[:6]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            title = safe_get(entry, 'title')
            link = safe_get(entry, 'link')
            summary = safe_get(entry, 'summary')
            # published -> try to get published_parsed
            published_dt = None
            if "published_parsed" in entry and entry.published_parsed:
                published_dt = datetime.datetime.utcfromtimestamp(time.mktime(entry.published_parsed))
            elif "updated_parsed" in entry and entry.updated_parsed:
                published_dt = datetime.datetime.utcfromtimestamp(time.mktime(entry.updated_parsed))
            collected.append({
                "title": title,
                "link": link,
                "summary": summary,
                "published_dt": published_dt,
                "source": source_name
            })

    if not collected:
        print("No items fetched from feeds.")
    items = choose_items(collected)

    # 今天日期
    today = datetime.datetime.utcnow().strftime("%Y%m%d")
    html_file = f"news/daily_news_{today}.html"
    rss_file = "news/news_feed.xml"

    # 生成 HTML（简易排版）
    html_parts = []
    html_parts.append("<!doctype html><html><head><meta charset='utf-8'><title>Daily News</title></head><body>")
    html_parts.append(f"<h1>Daily News Digest — {today} (Top {len(items)})</h1>")
    html_parts.append(f"<p>Generated (UTC): {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>")
    for it in items:
        pub_str = it["published_dt"].strftime("%Y-%m-%d %H:%M UTC") if it["published_dt"] else ""
        html_parts.append("<article style='margin-bottom:24px;'>")
        html_parts.append(f"<h3><a href='{html.escape(it['link'])}' target='_blank'>{html.escape(it['title'])}</a> <small>— {html.escape(it['source'])}</small></h3>")
        if pub_str:
            html_parts.append(f"<div><em>Published: {pub_str}</em></div>")
        html_parts.append(f"<p>{html.escape(it['summary'])}</p>")
        # 简单自动生成 Why it matters（基于关键字）
        why = "Relevant for ongoing international developments."
        text = (it["title"] + " " + it["summary"]).lower()
        if any(k in text for k in ["israel","gaza","palestine","hezbollah","iran","hamas"]):
            why = "Affects regional stability, humanitarian access and international diplomacy."
        elif any(k in text for k in ["trade","tariff","export","economic","inflation","fed","bank"]):
            why = "Could influence markets, trade flows and monetary policy."
        elif any(k in text for k in ["ai","quantum","technology","tech","google","apple","microsoft"]):
            why = "Impacts technology trends, regulation and competitive dynamics."
        elif any(k in text for k in ["climate","carbon","renewable","emissions"]):
            why = "Impacts climate policy and long-term sustainability planning."
        html_parts.append(f"<p><strong>Why it matters:</strong> {html.escape(why)}</p>")
        html_parts.append("</article>")

    html_parts.append("</body></html>")
    html_content = "\n".join(html_parts)

    # 生成 RSS XML（RSS 2.0）
    rss_items = []
    for it in items:
        title = html.escape(it["title"])
        link = html.escape(it["link"])
        summary = html.escape(it["summary"])
        if it["published_dt"]:
            pub = to_rfc2822(it["published_dt"])
        else:
            pub = to_rfc2822(datetime.datetime.utcnow())
        # 简单 why text used in description
        text = (it["title"] + " " + it["summary"]).lower()
        if any(k in text for k in ["israel","gaza","palestine","hezbollah","iran","hamas"]):
            why = "Affects regional stability, humanitarian access and international diplomacy."
        elif any(k in text for k in ["trade","tariff","export","economic","inflation","fed","bank"]):
            why = "Could influence markets, trade flows and monetary policy."
        elif any(k in text for k in ["ai","quantum","technology","tech","google","apple","microsoft"]):
            why = "Impacts technology trends, regulation and competitive dynamics."
        else:
            why = "Relevant for ongoing international developments."

        desc = f"<![CDATA[{it['summary']}<br/><strong>Why it matters:</strong> {why}]]>"
        rss_items.append(f"""  <item>
    <title>{title}</title>
    <link>{link}</link>
    <description>{desc}</description>
    <pubDate>{pub}</pubDate>
    <category>{it['source']}</category>
  </item>""")

    rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Daily News Digest - Top {len(items)}</title>
    <link>https://github.com/</link>
    <description>Daily curated international news (top {len(items)})</description>
    <language>en-us</language>
{''.join(rss_items)}
  </channel>
</rss>
"""

    # 写文件（确保目录存在）
    import os
    os.makedirs("news", exist_ok=True)

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(rss_file, "w", encoding="utf-8") as f:
        f.write(rss_content)

    print("Saved:", html_file)
    print("Saved:", rss_file)

if __name__ == "__main__":
    main()
