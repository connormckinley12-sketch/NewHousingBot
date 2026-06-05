#!/usr/bin/env python3
"""
Triangle Housing Guide Bot v2
Runs Mon/Wed/Fri — verified data, smart scoring, auto site updates

Pipeline:
1. Scrape verified primary sources (Wake County API, RSS feeds, municipal sites)
2. Deduplicate against 7-day cache
3. Score with 4-dimension Claude analysis
4. Write articles for top 5 items
5. Detect trends across all items
6. Generate market summary
7. Auto-update website via GitHub
8. Send intelligence digest email
"""

import os
import json
import hashlib
import logging
import signal
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

from scrapers import permits, market_data, local_news, new_construction, economic, schools
from utils.cache import load_cache, save_cache
from utils.claude_intelligence import score_items, write_article, detect_trends, generate_market_summary
from utils.email_sender import send_digest
from utils.site_updater import update_site


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def run_safe(name, fn, timeout=60):
    def handler(signum, frame):
        raise TimeoutError(f"{name} timed out")
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    try:
        result = fn()
        signal.alarm(0)
        return result
    except TimeoutError as e:
        log.error(f"  TIMEOUT: {e}")
        return []
    except Exception as e:
        log.error(f"  ERROR in {name}: {e}")
        signal.alarm(0)
        return []


def run():
    log.info("=== Triangle Housing Guide Bot v2 ===")
    log.info(f"Run time: {datetime.now().strftime('%A %B %d, %Y %H:%M')}")

    cache = load_cache()
    all_items = []

    SCRAPERS = [
        ("Permits & Zoning",    permits.scrape),
        ("Market Data",         market_data.scrape),
        ("Local News",          local_news.scrape),
        ("New Construction",    new_construction.scrape),
        ("Economic & Jobs",     economic.scrape),
        ("Schools",             schools.scrape),
    ]

    for category, fn in SCRAPERS:
        log.info(f"Scraping: {category}")
        items = run_safe(category, fn, timeout=60)
        new_items = []
        for item in items:
            key = md5(item.get("url", item.get("title", "")))
            if key not in cache:
                cache[key] = datetime.now().isoformat()
                item["category"] = item.get("category", category)
                new_items.append(item)
        log.info(f"  {len(new_items)} new / {len(items)} scraped")
        all_items.extend(new_items)

    if not all_items:
        log.info("No new items this run.")
        save_cache(cache)
        return

    log.info(f"\nTotal new items: {len(all_items)}")

    # Score with 4-dimension analysis
    log.info("Scoring with Claude 4-dimension analysis...")
    scored = score_items(all_items)
    relevant = [i for i in scored if i.get("score", 0) >= 6]
    log.info(f"  {len(relevant)} items scored >= 6")

    # Write articles for top 5
    top5 = sorted(relevant, key=lambda x: x.get("score",0), reverse=True)[:5]
    log.info(f"Writing articles for top {len(top5)} items...")
    for item in top5:
        article = write_article(item)
        if article:
            item["article"] = article
            log.info(f"  ✅ {item.get('title','')[:60]}")

    # Detect trends
    log.info("Detecting trends...")
    trends = detect_trends(scored) if len(scored) >= 5 else []
    log.info(f"  {len(trends)} trends detected")

    # Generate market summary
    log.info("Generating market summary...")
    market_summary = generate_market_summary(relevant) if relevant else ""

    # Auto-update website
    log.info("Updating website via GitHub...")
    site_updated = update_site(relevant, market_summary)
    log.info(f"  Site update: {'✅' if site_updated else '⚠️ manual update needed'}")

    # Send digest
    log.info("Sending email digest...")
    send_digest(relevant, trends, market_summary, site_updated)
    log.info("✅ Digest sent")

    save_cache(cache)
    log.info("=== Done ===")


if __name__ == "__main__":
    run()
