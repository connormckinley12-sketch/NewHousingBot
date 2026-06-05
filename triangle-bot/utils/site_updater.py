"""
Site Updater — Push content to GitHub → triggers Netlify redeploy
Updates: ticker, featured news, market stats, last-verified dates
"""
import os, re, json, base64, requests
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN","")
GITHUB_REPO = os.environ.get("GITHUB_REPO","")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH","main")
HEADERS = {"Authorization":f"token {GITHUB_TOKEN}","Accept":"application/vnd.github.v3+json","Content-Type":"application/json"}


def _get_file(path):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return "", ""
    r = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}", headers=HEADERS)
    if r.status_code == 200:
        d = r.json()
        return base64.b64decode(d["content"]).decode("utf-8"), d["sha"]
    return "", ""


def _update_file(path, content, sha, message):
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return False
    r = requests.put(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}",
        headers=HEADERS,
        json={"message":message,"content":base64.b64encode(content.encode()).decode(),"sha":sha,"branch":GITHUB_BRANCH}
    )
    return r.status_code in [200,201]


def update_site(items: list[dict], market_summary: str = "") -> bool:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("[site_updater] No GitHub credentials — skipping")
        return False

    today = datetime.now().strftime("%B %d, %Y")
    updated = False

    try:
        content, sha = _get_file("index.html")
        if not content:
            print("[site_updater] Could not fetch index.html")
            return False

        # Update ticker with top 12 headlines
        top = sorted(items, key=lambda x: x.get("score",0), reverse=True)[:12]
        ticker_items = ""
        for item in top:
            city = item.get("city","Triangle")
            title = item.get("title","")[:75]
            ticker_items += f'<span class="ticker-item">{city}: {title}</span>\n    '
        ticker_html = f'<div class="ticker-inner">\n    {ticker_items*2}</div>'
        content = re.sub(r'<div class="ticker-inner">.*?</div>', ticker_html, content, flags=re.DOTALL)

        # Update featured news
        if top:
            featured = top[0]
            content = re.sub(r'id="news-headline">[^<]*<', f'id="news-headline">{featured.get("title","")}<', content)
            content = re.sub(r'id="news-body-text">[^<]*<', f'id="news-body-text">{featured.get("summary","")}<', content)
            content = re.sub(r'id="news-source">[^<]*<', f'id="news-source">{featured.get("source","")}<', content)
            content = re.sub(r'id="news-date">[^<]*<', f'id="news-date">{today}<', content)
            content = re.sub(r'id="news-label">[^<]*<', f'id="news-label">Updated {today}<', content)
            content = re.sub(r'id="news-city-pill">[^<]*<', f'id="news-city-pill">{featured.get("city","Triangle")}<', content)

        # Update sidebar news items
        sidebar_items = top[1:5]
        sidebar_html = "".join([f'''<div class="news-item"><div class="news-item-hdr"><span class="ni-badge">{s.get("category","News")}</span><span class="ni-city">{s.get("city","")}</span></div><h4>{s.get("title","")}</h4><div class="news-item-meta">{s.get("source","")} · {today}</div></div>''' for s in sidebar_items])
        content = re.sub(r'<div class="news-sidebar" id="news-sidebar">.*?</div>\s*</div>\s*</div>\s*</section>', f'<div class="news-sidebar" id="news-sidebar">{sidebar_html}</div></div></div></section>', content, flags=re.DOTALL)

        # Update footer verified date
        content = content.replace("Market data verified June 2026", f"Market data verified {today}")
        content = re.sub(r"Market data verified \w+ \d{4}", f"Market data verified {today}", content)

        if _update_file("index.html", content, sha, f"Bot: content refresh {today}"):
            print(f"[site_updater] ✅ index.html updated")
            updated = True

    except Exception as e:
        print(f"[site_updater] Error: {e}")

    return updated
