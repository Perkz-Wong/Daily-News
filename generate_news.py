import feedparser
import datetime

# 新闻 RSS 源
sources = {
    "Reuters": "http://feeds.reuters.com/reuters/worldNews",
    "AFP": "https://www.afp.com/en/rss",
    "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Guardian": "https://www.theguardian.com/world/rss",
    "FoxNews": "http://feeds.foxnews.com/foxnews/world",
    "Independent": "https://www.independent.co.uk/news/world/rss"
}

news_items = []

# 抓取新闻
for source, url in sources.items():
    feed = feedparser.parse(url)
    for entry in feed.entries[:5]:  # 每个源先取5条
        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "summary": getattr(entry, "summary", ""),
            "source": source
        })

# 只保留 10 条新闻
news_items = news_items[:10]

# 格式化成 HTML
today = datetime.date.today().strftime("%Y-%m-%d")
html_content = f"<h1>Daily International News ({today})</h1><ul>"
for item in news_items:
    html_content += f"<li><b>{item['source']}</b>: <a href='{item['link']}'>{item['title']}</a><br>{item['summary']}</li><br>"
html_content += "</ul>"

# 写入文件
with open("news/daily_news.html", "w", encoding="utf-8") as f:
    f.write(html_content)
