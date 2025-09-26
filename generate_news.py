import feedparser
import datetime

# 定义 RSS 源
rss_feeds = [
    "https://www.reuters.com/rssFeed/worldNews",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.theguardian.com/world/rss",
    "https://www.france24.com/en/rss",
    "https://feeds.foxnews.com/foxnews/world",
    "https://www.independent.co.uk/news/world/rss"
]

articles = []

# 解析 RSS
for feed in rss_feeds:
    d = feedparser.parse(feed)
    for entry in d.entries[:5]:  # 每个源取前 5 条
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": getattr(entry, "summary", "No summary available.")
        })

# 获取今天日期 (UTC)
today = datetime.datetime.utcnow().strftime("%Y%m%d")

# 生成文件名，带日期
output_file = f"news/daily_news_{today}.html"

# 生成 HTML
html_content = "<html><head><meta charset='utf-8'><title>Daily News</title></head><body>"
html_content += f"<h1>Daily News Digest - {today}</h1><ul>"

for a in articles:
    html_content += f"<li><a href='{a['link']}' target='_blank'>{a['title']}</a><br>{a['summary']}</li><br>"

html_content += "</ul></body></html>"

# 写入文件
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ Saved: {output_file}")
