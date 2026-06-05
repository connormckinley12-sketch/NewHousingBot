"""
Local News — Reliable RSS-first approach
Sources: Apex Herald, Triangle Business Journal, WRAL, News & Observer,
         Town of Apex, Wake County, NCDOT
"""

import requests
import feedparser
import urllib3
urllib3.disable_warnings()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

RSS_SOURCES = [
    {"name": "Apex Herald", "url": "https://apexherald.com/feed/", "city": "Apex"},
    {"name": "Triangle Business Journal", "url": "https://www.bizjournals.com/triangle/news/rss.xml", "city": "Triangle-wide"},
    {"name": "WRAL News", "url": "https://www.wral.com/news/rss/", "city": "Triangle-wide"},
    {"name": "NC REALTORS", "url": "https://www.ncrealtors.org/feed/", "city": "Triangle-wide"},
]

MUNICIPAL_SOURCES = [
    {"name": "Town of Apex News", "url": "https://www.apexnc.org/CivicAlerts.aspx", "city": "Apex"},
    {"name": "Town of Apex Agendas", "url": "https://www.apexnc.org/AgendaCenter", "city": "Apex"},
    {"name": "Wake County News", "url": "https://www.wakegov.com/news", "city": "Triangle-wide"},
]

HOUSING_KEYWORDS = [
    "housing", "development", "zoning", "permit", "real estate", "construction",
    "subdivision", "neighborhood", "residential", "property", "homebuyer",
    "mortgage", "school", "commute", "apex", "cary", "holly springs",
    "raleigh", "durham", "chapel hill", "pittsboro", "wake county", "chatham"
]


def scrape() -> list[dict]:
    items = []
    items += _scrape_rss()
    items += _scrape_municipal()
    return items


def _scrape_rss() -> list[dict]:
    items = []
    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:20]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", source["url"])
                combined = (title + " " + summary).lower()

                if any(kw in combined for kw in HOUSING_KEYWORDS):
                    # Detect city
                    city = source["city"]
                    for c in ["Apex", "Cary", "Holly Springs", "Raleigh", "Durham", "Chapel Hill", "Pittsboro"]:
                        if c.lower() in combined:
                            city = c
                            break

                    items.append({
                        "title": title,
                        "url": link,
                        "summary": summary[:500] if summary else title,
                        "source": source["name"],
                        "city": city,
                        "data_type": "local_news",
                        "verified": True,
                    })
        except Exception as e:
            print(f"[news/{source['name']}] Error: {e}")
    return items


def _scrape_municipal() -> list[dict]:
    from bs4 import BeautifulSoup
    items = []
    for source in MUNICIPAL_SOURCES:
        try:
            r = requests.get(source["url"], headers=HEADERS, timeout=10, verify=False)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            for el in soup.select("article, .news-item, li, .catAgendaRow, tr")[:15]:
                title_el = el.select_one("a, h2, h3, h4, td")
                link_el = el.select_one("a[href]")
                if title_el:
                    title = title_el.get_text(strip=True)
                    url = link_el["href"] if link_el else source["url"]
                    if url.startswith("/"):
                        base = "/".join(source["url"].split("/")[:3])
                        url = base + url
                    if len(title) > 10:
                        items.append({
                            "title": f"{source['name']}: {title}",
                            "url": url,
                            "summary": title,
                            "source": source["name"],
                            "city": source["city"],
                            "data_type": "municipal",
                            "verified": True,
                        })
        except Exception as e:
            print(f"[news/{source['name']}] Error: {e}")
    return items
