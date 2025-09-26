import feedparser
import openai
import os
from datetime import datetime

# ---------------------------
# 安全获取字段的函数
# ---------------------------
def safe_get(entry, key):
    return entry.get(key, "")

# ---------------------------
# 主函数
# ---------------------------
def main():
    # 设置 OpenAI API Key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # RSS 源列表
    feeds = [
        "http://rss.cnn.com/rss/edition.rss",
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://www.theguardian.com/world/rss",
    ]

    articles = []

    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            title = safe_get(entry, "title")
            summary = safe_get(entry, "summary")
            link = safe_get(entry, "link")
            articles.append(f"- **{title}**\n{summary}\n[Read more]({link})\n")

    # 生成新闻内容
    news_content = "\n".join(articles)

    # 用 OpenAI 总结
    prompt = f"Summarize the following news articles into a short daily news briefing:\n\n{news_content}"

    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500,
        temperature=0.7
    )

    daily_news = response.choices[0].text.strip()

    # 保存到 Markdown 文件
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"news_{today}.md"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# Daily News - {today}\n\n")
        f.write(daily_news)

    print(f"✅ News generated and saved to {filename}")


if __name__ == "__main__":
    main()
