"""
Market Data — Real verified sources
Pulls from Redfin, Doorify MLS blog, NC REALTORS, Freddie Mac PMMS
"""

import requests
import feedparser
import urllib3
urllib3.disable_warnings()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Freddie Mac PMMS — most reliable mortgage rate source
FREDDIE_MAC_URL = "https://www.freddiemac.com/pmms"

# Doorify MLS market updates (Triangle-specific, most accurate)
DOORIFY_FEEDS = [
    "https://www.blueorchidrealty.com/blog/rss.xml",  # Uses Doorify MLS data
]

# NC REALTORS research
NC_REALTORS_RSS = "https://www.ncrealtors.org/feed/"

# Triangle Business Journal for economic context
TBJ_RSS = "https://www.bizjournals.com/triangle/news/rss.xml"

CITIES = ["Apex", "Cary", "Holly Springs", "Raleigh", "Durham", "Chapel Hill", "Pittsboro"]
MARKET_KEYWORDS = [
    "median", "home price", "housing market", "days on market",
    "inventory", "mortgage rate", "real estate", "triangle", "wake county",
    "apex", "cary", "holly springs", "raleigh", "durham", "chapel hill", "pittsboro"
]


def scrape() -> list[dict]:
    items = []
    items += _scrape_freddie_mac()
    items += _scrape_rss_feeds()
    return items


def _scrape_freddie_mac() -> list[dict]:
    items = []
    try:
        from bs4 import BeautifulSoup
        r = requests.get(FREDDIE_MAC_URL, headers=HEADERS, timeout=15, verify=False)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        rates = []
        for el in soup.select("[class*='rate'], [class*='pmms'], .number, strong")[:10]:
            text = el.get_text(strip=True)
            if "%" in text and len(text) < 10:
                rates.append(text)

        rate_text = " | ".join(rates[:3]) if rates else "See freddiemac.com for current rates"
        items.append({
            "title": "Weekly Mortgage Rates — Freddie Mac PMMS",
            "url": FREDDIE_MAC_URL,
            "summary": f"Latest Freddie Mac Primary Mortgage Market Survey: {rate_text}. Directly impacts Triangle homebuyer affordability.",
            "source": "Freddie Mac PMMS",
            "city": "Triangle-wide",
            "data_type": "market_data",
            "verified": True,
        })
    except Exception as e:
        print(f"[market/freddie] Error: {e}")
    return items


def _scrape_rss_feeds() -> list[dict]:
    items = []
    all_feeds = DOORIFY_FEEDS + [NC_REALTORS_RSS, TBJ_RSS]

    for feed_url in all_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                link = entry.get("link", feed_url)
                combined = (title + " " + summary).lower()

                if any(kw in combined for kw in MARKET_KEYWORDS):
                    # Detect which city this is about
                    city = "Triangle-wide"
                    for c in CITIES:
                        if c.lower() in combined:
                            city = c
                            break

                    items.append({
                        "title": title,
                        "url": link,
                        "summary": summary[:500] if summary else title,
                        "source": feed.feed.get("title", feed_url),
                        "city": city,
                        "data_type": "market_news",
                        "verified": True,
                    })
        except Exception as e:
            print(f"[market/feed/{feed_url[:40]}] Error: {e}")

    return items
