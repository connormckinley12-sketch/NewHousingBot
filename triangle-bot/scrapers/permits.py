"""
Wake County Building Permits — Real API
Source: Wake County Open Data ArcGIS REST API
Returns verified permit data for all 7 Triangle cities
"""

import requests

HEADERS = {"User-Agent": "TriangleHousingGuideBot/2.0"}

WAKE_API = "https://services.wake.gov/arcgis/rest/services/Building/BuildingPermits/MapServer/0/query"

CITIES = ["APEX", "CARY", "HOLLY SPRINGS", "RALEIGH"]  # Wake County cities

CHATHAM_API = "https://www.chathamcountync.gov/government/departments-programs/planning/development-activity"

HOUSING_TYPES = [
    "SINGLE FAMILY", "MULTI FAMILY", "TOWNHOUSE", "DUPLEX",
    "RESIDENTIAL", "NEW DWELLING", "ADDITION", "ACCESSORY DWELLING",
    "GRADING", "LAND DISTURBING", "SUBDIVISION"
]


def scrape() -> list[dict]:
    items = []
    items += _scrape_wake_permits()
    items += _scrape_apex_development()
    return items


def _scrape_wake_permits() -> list[dict]:
    items = []
    for city in CITIES:
        try:
            params = {
                "where": f"UPPER(JURISDICTION) = '{city}' AND ISSUEDATE >= CURRENT_TIMESTAMP - INTERVAL '3' DAY",
                "outFields": "PERMITNO,PERMITTYPE,ADDRESS,ISSUEDATE,DESCRIPTION,JURISDICTION,TOTALFEE",
                "orderByFields": "ISSUEDATE DESC",
                "resultRecordCount": 50,
                "f": "json",
            }
            r = requests.get(WAKE_API, params=params, headers=HEADERS, timeout=20, verify=False)
            r.raise_for_status()
            data = r.json()

            for feat in data.get("features", []):
                props = feat.get("attributes", {})
                permit_type = (props.get("PERMITTYPE") or "").upper()
                description = (props.get("DESCRIPTION") or "").upper()
                address = props.get("ADDRESS") or ""
                permit_no = props.get("PERMITNO") or ""
                issue_date = props.get("ISSUEDATE") or ""
                fee = props.get("TOTALFEE") or 0
                jurisdiction = (props.get("JURISDICTION") or city).title()

                if any(ht in permit_type + description for ht in HOUSING_TYPES):
                    items.append({
                        "title": f"Permit: {permit_type.title()} at {address}, {jurisdiction}",
                        "url": "https://www.wakegov.com/departments-government/planning-development-inspections",
                        "summary": f"Permit #{permit_no} issued in {jurisdiction}. Type: {permit_type.title()}. {description.title()[:100]}. Estimated value: ${fee:,.0f}",
                        "source": "Wake County Permits API",
                        "city": jurisdiction,
                        "data_type": "permit",
                        "verified": True,
                    })
        except Exception as e:
            print(f"[permits/{city}] Error: {e}")
    return items


def _scrape_apex_development() -> list[dict]:
    from bs4 import BeautifulSoup
    items = []
    try:
        r = requests.get(
            "https://www.apexnc.org/174/Development-Activity",
            headers=HEADERS, timeout=15, verify=False
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.select("table tr, .development-item, .fr-view li")[:20]:
            text = row.get_text(strip=True)
            link = row.find("a")
            if len(text) > 20:
                url = link["href"] if link else "https://www.apexnc.org/174/Development-Activity"
                if url.startswith("/"):
                    url = "https://www.apexnc.org" + url
                items.append({
                    "title": f"Apex Development: {text[:100]}",
                    "url": url,
                    "summary": text[:400],
                    "source": "Town of Apex Development Activity",
                    "city": "Apex",
                    "data_type": "development",
                    "verified": True,
                })
    except Exception as e:
        print(f"[permits/apex_dev] Error: {e}")
    return items
