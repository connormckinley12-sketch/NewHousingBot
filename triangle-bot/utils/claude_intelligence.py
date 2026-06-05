"""
Claude Intelligence Layer
- Advanced 4-dimension scoring
- Auto-write articles for top items  
- Trend detection across all items
- Market summary generation
"""
import os, json
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SCORE_PROMPT = """You are the editorial AI for Triangle Housing Guide, covering Apex, Cary, Raleigh, Durham, Chapel Hill, Holly Springs, and Pittsboro NC.

Score each item on 4 dimensions (1-10):
1. LOCAL_RELEVANCE (35%) — How directly does this affect Triangle NC housing decisions?
2. SEARCH_INTENT (25%) — Would an active homebuyer/seller Google this?
3. FRESHNESS_VALUE (25%) — Is timing critical? Breaking news scores higher.
4. REVENUE_SIGNAL (15%) — Does this lead to an agent or vendor conversion?

Weighted score = (lr*0.35) + (si*0.25) + (fv*0.25) + (rs*0.15)

Also assign category: Market Data | New Development | Permits & Zoning | Schools | Financial | Town News | Infrastructure | Economic Growth
And city: Apex | Cary | Holly Springs | Raleigh | Durham | Chapel Hill | Pittsboro | Triangle-wide

Return ONLY a JSON array, no markdown:
[{"title":"SEO-friendly title","url":"original","summary":"2-3 sentence buyer-focused summary","local_relevance":8,"search_intent":7,"freshness_value":9,"revenue_signal":6,"score":7.85,"category":"New Development","city":"Apex","source":"original source"}]"""

ARTICLE_PROMPT = """You are a staff writer for Triangle Housing Guide.

Write a 150-200 word news article. Rules:
- Lead with the most important fact (answer-first)
- Include specific local details (addresses, prices, numbers when available)  
- Take a clear editorial point of view — what does this mean for Triangle buyers/sellers?
- End with one actionable takeaway
- Clean, authoritative tone — not salesy, not clickbait
- Do NOT include a headline

Return ONLY the article text."""

TREND_PROMPT = """You are the data analyst for Triangle Housing Guide.

Analyze this batch of Triangle housing items and identify 3-5 notable trends. For each:
- State it as a specific, data-driven finding
- Explain what it signals for Triangle buyers/sellers  
- Rate significance: High | Medium | Low
- List which cities are affected

Return ONLY a JSON array:
[{"trend":"specific finding","signal":"buyer/seller implication","significance":"High","cities_affected":["Apex","Holly Springs"]}]"""

MARKET_SUMMARY_PROMPT = """You are the market analyst for Triangle Housing Guide.

Based on this batch of Triangle NC housing data, write a 200-word market summary covering:
1. Overall Triangle market temperature (hot/warm/balanced/cooling)
2. Top 2-3 developments worth watching
3. What buyers should know right now
4. What sellers should know right now

Write in a clear, direct editorial voice. No fluff. Return only the summary text."""


def score_items(items: list[dict], batch_size=20) -> list[dict]:
    scored = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        scored.extend(_score_batch(batch))
    return scored


def _score_batch(items):
    try:
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=8000,
            system=SCORE_PROMPT,
            messages=[{"role":"user","content":f"Score these {len(items)} items:\n\n{json.dumps(items,indent=2)}"}]
        )
        raw = msg.content[0].text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[intelligence/score] Error: {e}")
        return [{**i, "score":5, "category":"General", "city":"Triangle-wide"} for i in items]


def write_article(item: dict) -> str:
    try:
        prompt = f"Title: {item.get('title','')}\nSummary: {item.get('summary','')}\nSource: {item.get('source','')}\nCity: {item.get('city','')}\n\nWrite the article:"
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            system=ARTICLE_PROMPT,
            messages=[{"role":"user","content":prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"[intelligence/article] Error: {e}")
        return ""


def detect_trends(items: list[dict]) -> list[dict]:
    try:
        summary = json.dumps([{"title":i.get("title",""),"category":i.get("category",""),"city":i.get("city",""),"summary":i.get("summary","")} for i in items], indent=2)
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2000,
            system=TREND_PROMPT,
            messages=[{"role":"user","content":f"Analyze {len(items)} Triangle housing items:\n\n{summary}"}]
        )
        raw = msg.content[0].text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[intelligence/trends] Error: {e}")
        return []


def generate_market_summary(items: list[dict]) -> str:
    try:
        summary = json.dumps([{"title":i.get("title",""),"category":i.get("category",""),"city":i.get("city",""),"summary":i.get("summary",""),"score":i.get("score",0)} for i in items[:30]], indent=2)
        msg = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=500,
            system=MARKET_SUMMARY_PROMPT,
            messages=[{"role":"user","content":f"Generate market summary from {len(items)} items:\n\n{summary}"}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"[intelligence/summary] Error: {e}")
        return ""
