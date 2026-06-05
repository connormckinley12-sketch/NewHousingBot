"""URL deduplication cache — 7 day TTL for 3-day run cycle"""
import json, os
from datetime import datetime, timedelta

CACHE_FILE = os.environ.get("CACHE_FILE", "/data/cache.json")
CACHE_TTL_DAYS = 7  # Keep 7 days so we don't re-send items from last run

def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        return {}
    try:
        with open(CACHE_FILE) as f:
            raw = json.load(f)
        cutoff = (datetime.now() - timedelta(days=CACHE_TTL_DAYS)).isoformat()
        return {k: v for k, v in raw.items() if isinstance(v, str) and v > cutoff}
    except:
        return {}

def save_cache(cache: dict):
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        now = datetime.now().isoformat()
        upgraded = {k: (now if v is True else v) for k, v in cache.items()}
        with open(CACHE_FILE, "w") as f:
            json.dump(upgraded, f, indent=2)
    except Exception as e:
        print(f"[cache] Save error: {e}")
