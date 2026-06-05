"""
Economic & Jobs — Job announcements, population growth, employer news
Sources: NC Commerce, Wake County Economic Dev, Triangle Business Journal, Research Triangle Park
"""

import feedparser
import requests
import urllib3
urllib3.disable_warnings()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

ECONOMIC_FEEDS = [
    {"name": "NC Commerce Dept", "url": "https://www.nccommerce.com/news/rss.xml"},
    {"name": "Triangle Business Journal", "url": "https://www.bizjournals.com/triangle/news/rss.xml"},
    {"name": "Research Triangle Park", "url": "https://rtp.org/feed/"},
    {"name": "Wake County Economic Dev", "url": "https://www.wake.gov/rss/news"},
]

ECONOMIC_KEYWORDS = [
    "jobs", "employment", "company", "relocat", "expand", "headquarter",
    "economic development", "rtp", "research triangle", "biotech", "tech",
    "population", "growth", "apex", "cary", "raleigh", "triangle",
    "wake county", "chatham", "announce", "invest"
]

CITIES = ["Apex", "Cary", "Holly Springs", "Raleigh", "Durham", "Chapel Hill", "Pittsboro"]


def scrape() -> list[dict]:
    items = []
    for source in ECONOMIC_FEEDS:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", source["url"])
                combined = (title + " " + summary).lower()

                if any(kw in combined for kw in ECONOMIC_KEYWORDS):
                    city = "Triangle-wide"
                    for c in CITIES:
                        if c.lower() in combined:
                            city = c
                            break

                    items.append({
                        "title": title,
                        "url": link,
                        "summary": summary[:500] if summary else title,
                        "source": source["name"],
                        "city": city,
                        "data_type": "economic",
                        "verified": True,
                    })
        except Exception as e:
            print(f"[economic/{source['name']}] Error: {e}")
    return items
