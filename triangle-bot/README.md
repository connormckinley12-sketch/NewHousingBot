# Triangle Housing Guide Bot v2

Runs Mon/Wed/Fri at 7AM ET. Scrapes verified primary sources, scores with Claude AI, auto-updates website, sends digest.

## Environment Variables (Railway)

| Variable | Value |
|---|---|
| ANTHROPIC_API_KEY | Your Anthropic key |
| SENDGRID_API_KEY | Your SendGrid key |
| FROM_EMAIL | bot@trianglehousingguide.com |
| TO_EMAIL | Your email |
| CACHE_FILE | /data/cache.json |
| GITHUB_TOKEN | Personal access token (repo scope) |
| GITHUB_REPO | connormckinley12-sketch/HousingGuide_Bot1 |
| GITHUB_BRANCH | main |

## Cron Schedule (Railway)
```
0 12 1,3,5 * *   →   python main.py
```
(Mon/Wed/Fri at 7AM ET = 12:00 UTC)

## Sources
- Wake County Building Permits API (real-time)
- Doorify MLS market data
- Freddie Mac PMMS mortgage rates
- Town of Apex development activity
- Wake County planning/rezoning
- Apex Herald RSS
- Triangle Business Journal RSS
- NC REALTORS RSS
- WCPSS school news
- NC Commerce economic announcements
- Research Triangle Park feed

## Pipeline
1. Scrape 6 source categories with 60s timeout each
2. Deduplicate against 7-day cache
3. Claude 4-dimension scoring (local relevance, search intent, freshness, revenue signal)
4. Auto-write 150-200 word articles for top 5 items
5. AI trend detection across all items
6. AI market summary generation
7. Push to GitHub → Netlify auto-redeploys
8. Send HTML email digest
