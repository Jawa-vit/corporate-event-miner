"""
Task (a): Crawl / download / extract financial news articles.

Reads public RSS feeds of free financial-news and regulatory websites,
downloads each article page and extracts the readable text with BeautifulSoup.
Falls back to the RSS summary if a page cannot be downloaded.
"""
import json
import time
import urllib.robotparser
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (Student Research Project)"
HEADERS = {"User-Agent": USER_AGENT}

# Free news + regulatory sources (Indian and foreign). URLs can change over time -
# if a feed returns nothing, just replace it with another public RSS URL.
FEEDS = {
    "BBC Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "SEC Press Releases": "https://www.sec.gov/news/pressreleases.rss",
    "Economic Times": "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    "Moneycontrol": "https://www.moneycontrol.com/rss/business.xml",
    "Livemint Companies": "https://www.livemint.com/rss/companies",
}

_robots_cache = {}


def allowed_by_robots(url: str) -> bool:
    """Be a polite crawler: obey robots.txt."""
    parts = urlparse(url)
    base = f"{parts.scheme}://{parts.netloc}"
    if base not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.set_url(base + "/robots.txt")
            rp.read()
        except Exception:
            rp = None
        _robots_cache[base] = rp
    rp = _robots_cache[base]
    return True if rp is None else rp.can_fetch(USER_AGENT, url)


def extract_text(html: str) -> str:
    """Pull the main readable paragraphs out of an HTML page."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    container = soup.find("article") or soup
    paras = [p.get_text(" ", strip=True) for p in container.find_all("p")]
    paras = [p for p in paras if len(p) > 40]
    return "\n".join(paras)


def fetch_article_text(url: str, timeout: int = 15) -> str:
    if not allowed_by_robots(url):
        return ""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return extract_text(r.text)
    except Exception as exc:
        print(f"   ! could not download {url}: {exc}")
        return ""


def crawl(feeds=None, per_feed: int = 15, delay: float = 1.0):
    """Return a list of article dicts: source, title, url, published, text."""
    feeds = feeds or FEEDS
    seen, articles = set(), []
    for source, feed_url in feeds.items():
        print(f"[crawl] {source}")
        parsed = feedparser.parse(feed_url, agent=USER_AGENT)
        for entry in parsed.entries[:per_feed]:
            url = entry.get("link", "")
            title = entry.get("title", "").strip()
            if not url or url in seen or title in seen:
                continue
            seen.update([url, title])
            summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)
            text = fetch_article_text(url) or summary
            articles.append({
                "source": source,
                "title": title,
                "url": url,
                "published": entry.get("published", ""),
                "text": text,
            })
            time.sleep(delay)
    print(f"[crawl] collected {len(articles)} articles")
    return articles


def load_sample(path="data/sample_articles.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_articles(articles, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
