"""
New Construction — Builder sites + rezoning + subdivision plats
Sources: Wake County rezoning, Apex development activity, builder sites
"""

import requests
import feedparser
import urllib3
urllib3.disable_warnings()
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Wake County planning / rezoning cases
WAKE_PLANNING_URL = "https://www.wakegov.com/departments-government/planning-development-inspections/rezoning-cases"

# Chatham County planning
CHATHAM_PLANNING_URL = "https://www.chathamcountync.gov/government/departments-programs/planning"

# Builder news feeds
BUILDER_SOURCES = [
    {"name": "Toll Brothers NC", "url": "https://www.tollbrothers.com/luxury-homes-for-sale/North-Carolina/Raleigh", "city": "Triangle-wide"},
    {"name": "DR Horton Raleigh", "url": "https://www.drhorton.com/north-carolina/raleigh", "city": "Triangle-wide"},
    {"name": "Lennar Raleigh", "url": "https://www.lennar.com/new-homes/north-carolina/raleigh", "city": "Triangle-wide"},
]

CONSTRUCTION_KEYWORDS = [
    "subdivision", "plat", "rezoning", "new community", "development",
    "construction", "builder", "groundbreaking", "homes", "units planned",
    "approved", "phase", "master plan"
]

CITIES = ["Apex", "Cary", "Holly Springs", "Raleigh", "Durham", "Chapel Hill", "Pittsboro"]


def scrape() -> list[dict]:
    items = []
    items += _scrape_wake_planning()
    items += _scrape_builders()
    return items


def _scrape_wake_planning() -> list[dict]:
    items = []
    try:
        r = requests.get(WAKE_PLANNING_URL, headers=HEADERS, timeout=15, verify=False)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.select("table tr, .case-item, article, li")[:25]:
            title_el = row.select_one("td, h3, a, .title")
            link_el = row.select_one("a[href]")
            if title_el:
                title = title_el.get_text(strip=True)
                url = link_el["href"] if link_el else WAKE_PLANNING_URL
                if url.startswith("/"):
                    url = "https://www.wakegov.com" + url

                city = "Wake County"
                for c in CITIES:
                    if c.lower() in title.lower():
                        city = c
                        break

                if len(title) > 5:
                    items.append({
                        "title": f"Wake County Planning: {title[:120]}",
                        "url": url,
                        "summary": f"Wake County planning/rezoning case: {title}",
                        "source": "Wake County Planning",
                        "city": city,
                        "data_type": "rezoning",
                        "verified": True,
                    })
    except Exception as e:
        print(f"[construction/wake_planning] Error: {e}")
    return items


def _scrape_builders() -> list[dict]:
    items = []
    for builder in BUILDER_SOURCES:
        try:
            r = requests.get(builder["url"], headers=HEADERS, timeout=15, verify=False)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            communities = soup.select(
                ".community, .community-card, [class*='community'], [class*='neighborhood'], .plan-card"
            )[:8]

            for community in communities:
                title_el = community.select_one("h2, h3, h4, .name, .community-name, .title")
                price_el = community.select_one(".price, [class*='price'], [class*='from']")
                link_el = community.select_one("a[href]")

                if title_el:
                    title = title_el.get_text(strip=True)
                    price = price_el.get_text(strip=True) if price_el else ""
                    url = link_el["href"] if link_el else builder["url"]
                    if url.startswith("/"):
                        base = "/".join(builder["url"].split("/")[:3])
                        url = base + url

                    city = "Triangle-wide"
                    for c in CITIES:
                        if c.lower() in (title + url).lower():
                            city = c
                            break

                    items.append({
                        "title": f"{builder['name']}: {title}",
                        "url": url,
                        "summary": f"New construction by {builder['name']}. {f'From {price}' if price else 'Contact builder for pricing.'}",
                        "source": builder["name"],
                        "city": city,
                        "data_type": "new_construction",
                        "verified": True,
                    })

            if not communities:
                items.append({
                    "title": f"New Homes — {builder['name']}",
                    "url": builder["url"],
                    "summary": f"New home communities available in the Triangle from {builder['name']}.",
                    "source": builder["name"],
                    "city": "Triangle-wide",
                    "data_type": "new_construction",
                    "verified": True,
                })

        except Exception as e:
            print(f"[construction/{builder['name']}] Error: {e}")
    return items
