"""
Schools — WCPSS, Chapel Hill-Carrboro, Durham Public Schools
Sources: district websites, boundary changes, new school announcements
"""

import requests
import feedparser
import urllib3
urllib3.disable_warnings()
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SCHOOL_SOURCES = [
    {"name": "WCPSS News", "url": "https://www.wcpss.net/site/handlers/rss.ashx?moduleinstanceid=26953&pageid=18541&feed=rss", "city": "Triangle-wide"},
    {"name": "WCPSS Alerts", "url": "https://www.wcpss.net/CivicAlerts.aspx", "city": "Triangle-wide"},
    {"name": "Chapel Hill-Carrboro Schools", "url": "https://www.chccs.k12.nc.us/news", "city": "Chapel Hill"},
]

SCHOOL_KEYWORDS = [
    "school", "boundary", "enrollment", "district", "elementary", "middle",
    "high school", "wcpss", "magnet", "reassignment", "new school",
    "opening", "capacity", "student", "teacher"
]


def scrape() -> list[dict]:
    items = []
    for source in SCHOOL_SOURCES:
        try:
            if "rss" in source["url"] or source["url"].endswith(".xml"):
                feed = feedparser.parse(source["url"])
                for entry in feed.entries[:10]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    link = entry.get("link", source["url"])
                    combined = (title + " " + summary).lower()
                    if any(kw in combined for kw in SCHOOL_KEYWORDS):
                        items.append({
                            "title": f"{source['name']}: {title}",
                            "url": link,
                            "summary": summary[:400] if summary else title,
                            "source": source["name"],
                            "city": source["city"],
                            "data_type": "schools",
                            "verified": True,
                        })
            else:
                r = requests.get(source["url"], headers=HEADERS, timeout=10, verify=False)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "html.parser")
                for el in soup.select("article, .news-item, li, h3")[:10]:
                    title_el = el.select_one("a, h3, h4")
                    link_el = el.select_one("a[href]")
                    if title_el:
                        title = title_el.get_text(strip=True)
                        combined = title.lower()
                        url = link_el["href"] if link_el else source["url"]
                        if url.startswith("/"):
                            base = "/".join(source["url"].split("/")[:3])
                            url = base + url
                        if any(kw in combined for kw in SCHOOL_KEYWORDS) and len(title) > 10:
                            items.append({
                                "title": f"{source['name']}: {title}",
                                "url": url,
                                "summary": title,
                                "source": source["name"],
                                "city": source["city"],
                                "data_type": "schools",
                                "verified": True,
                            })
        except Exception as e:
            print(f"[schools/{source['name']}] Error: {e}")
    return items
