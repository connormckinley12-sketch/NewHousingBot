"""Email digest with market summary, trends, articles, and scored items"""
import os
from datetime import datetime
from collections import defaultdict
import sendgrid
from sendgrid.helpers.mail import Mail

SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", "bot@trianglehousingguide.com")
TO_EMAIL = os.environ["TO_EMAIL"]

ICONS = {"Market Data":"📊","New Development":"🏗️","Permits & Zoning":"📋","Schools":"🏫","Financial":"💰","Town News":"🏛️","Infrastructure":"🚧","Economic Growth":"📈","General":"📰"}
SIG_COLORS = {"High":"#22c55e","Medium":"#f59e0b","Low":"#94a3b8"}


def send_digest(items, trends=None, market_summary="", site_updated=False):
    today = datetime.now().strftime("%B %d, %Y")
    subject = f"Triangle Housing Guide — Intelligence Digest | {today}"
    html = _build_html(items, trends or [], market_summary, site_updated, today)
    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    msg = Mail(from_email=FROM_EMAIL, to_emails=TO_EMAIL, subject=subject, html_content=html)
    r = sg.client.mail.send.post(request_body=msg.get())
    print(f"[email] SendGrid: {r.status_code}")


def _build_html(items, trends, market_summary, site_updated, date):
    by_cat = defaultdict(list)
    for item in sorted(items, key=lambda x: x.get("score",0), reverse=True):
        by_cat[item.get("category","General")].append(item)

    total = len(items)
    high = sum(1 for i in items if i.get("score",0) >= 7)
    site_badge = '<span style="background:#22c55e;color:white;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600">✅ Site updated</span>' if site_updated else '<span style="background:#f59e0b;color:white;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:600">⚠️ Review & update manually</span>'

    # Market summary block
    summary_html = ""
    if market_summary:
        summary_html = f'''<div style="background:#1e3a5f;border-radius:10px;padding:20px;margin-bottom:20px">
          <h2 style="color:#93c5fd;font-size:13px;font-weight:600;letter-spacing:1px;text-transform:uppercase;margin:0 0 10px 0">📊 AI Market Summary</h2>
          <p style="color:rgba(255,255,255,.85);font-size:14px;line-height:1.7;margin:0">{market_summary}</p>
        </div>'''

    # Trends block
    trends_html = ""
    if trends:
        trends_html = '<div style="margin-bottom:20px"><h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0 0 12px 0;padding-bottom:8px;border-bottom:2px solid #e2e8f0">📈 Trend analysis</h2>'
        for t in trends:
            color = SIG_COLORS.get(t.get("significance","Low"),"#94a3b8")
            cities = ", ".join(t.get("cities_affected",[]))
            trends_html += f'''<div style="border-left:3px solid {color};padding:10px 14px;margin-bottom:8px;background:#f8fafc;border-radius:0 6px 6px 0">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                <span style="font-size:13px;font-weight:600;color:#1e293b">{t.get("trend","")}</span>
                <span style="background:{color};color:white;border-radius:10px;padding:1px 8px;font-size:10px;font-weight:700">{t.get("significance","")}</span>
              </div>
              <p style="font-size:12px;color:#475569;margin:0 0 3px 0">{t.get("signal","")}</p>
              {f'<span style="font-size:10px;color:#94a3b8">Cities: {cities}</span>' if cities else ""}
            </div>'''
        trends_html += '</div>'

    # Content sections
    sections = ""
    for cat, cat_items in sorted(by_cat.items()):
        icon = ICONS.get(cat,"📰")
        items_html = ""
        for item in cat_items:
            score = item.get("score",0)
            sc = "#22c55e" if score>=8 else "#f59e0b" if score>=6 else "#94a3b8"
            city_pill = f'<span style="background:#e2e8f0;color:#475569;border-radius:3px;padding:1px 6px;font-size:10px;margin-left:6px">{item.get("city","")}</span>' if item.get("city") else ""
            article = f'<div style="background:#f1f5f9;border-radius:6px;padding:10px 12px;margin:8px 0;font-size:12px;color:#475569;line-height:1.65;font-style:italic">{item["article"]}</div>' if item.get("article") else ""
            score_detail = f'<div style="font-size:10px;color:#94a3b8;margin-top:3px">LR:{item.get("local_relevance","-")} · SI:{item.get("search_intent","-")} · FV:{item.get("freshness_value","-")} · RS:{item.get("revenue_signal","-")}</div>' if item.get("local_relevance") else ""

            items_html += f'''<div style="border-left:3px solid {sc};padding:12px 16px;margin-bottom:12px;background:#f8fafc;border-radius:0 6px 6px 0">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
                <div style="flex:1"><a href="{item.get('url','#')}" style="font-weight:600;color:#1e293b;text-decoration:none;font-size:14px;line-height:1.4">{item.get('title','')}</a>{city_pill}</div>
                <span style="background:{sc};color:white;border-radius:12px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:10px;white-space:nowrap">{round(score,1)}/10</span>
              </div>
              <p style="color:#475569;font-size:13px;margin:0 0 4px 0;line-height:1.5">{item.get('summary','')}</p>
              {article}
              <span style="color:#94a3b8;font-size:11px">📌 {item.get('source','')} · Verified data</span>
              {score_detail}
            </div>'''

        sections += f'''<div style="margin-bottom:24px">
          <h2 style="color:#0f172a;font-size:15px;font-weight:700;margin:0 0 12px 0;padding-bottom:8px;border-bottom:2px solid #e2e8f0">{icon} {cat} <span style="color:#94a3b8;font-size:12px;font-weight:400">({len(cat_items)})</span></h2>
          {items_html}
        </div>'''

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<div style="max-width:680px;margin:0 auto;padding:24px 16px">
  <div style="background:linear-gradient(135deg,#1e3a5f,#0f2444);border-radius:12px;padding:28px;margin-bottom:20px;text-align:center">
    <div style="font-size:24px;margin-bottom:6px">🏡</div>
    <h1 style="color:white;margin:0 0 4px 0;font-size:20px;font-weight:800">Triangle Housing Guide</h1>
    <p style="color:#93c5fd;margin:0 0 10px 0;font-size:12px">Intelligence Digest — {date} · Runs Mon/Wed/Fri</p>
    {site_badge}
  </div>
  <div style="background:white;border-radius:8px;padding:12px 18px;margin-bottom:18px;display:flex;gap:16px;border:1px solid #e2e8f0;text-align:center">
    <div style="flex:1"><div style="font-size:20px;font-weight:800;color:#1e3a5f">{total}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase">Total items</div></div>
    <div style="width:1px;background:#e2e8f0"></div>
    <div style="flex:1"><div style="font-size:20px;font-weight:800;color:#22c55e">{high}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase">Score 7+</div></div>
    <div style="width:1px;background:#e2e8f0"></div>
    <div style="flex:1"><div style="font-size:20px;font-weight:800;color:#f59e0b">{len(trends)}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase">Trends</div></div>
    <div style="width:1px;background:#e2e8f0"></div>
    <div style="flex:1"><div style="font-size:20px;font-weight:800;color:#8b5cf6">{len(by_cat)}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase">Categories</div></div>
  </div>
  <div style="background:white;border-radius:12px;padding:20px;border:1px solid #e2e8f0">
    {summary_html}{trends_html}{sections}
  </div>
  <div style="text-align:center;padding:16px;color:#94a3b8;font-size:11px">
    Triangle Housing Guide Bot v2 · Mon/Wed/Fri · All data from verified primary sources<br>
    Wake County API · Doorify MLS · Freddie Mac PMMS · NC REALTORS · Apex Herald
  </div>
</div></body></html>'''
