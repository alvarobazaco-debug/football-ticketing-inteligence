"""
fetch_clubs.py
==============
Descarga los equipos de las principales ligas europeas desde TheSportsDB (gratuita)
y actualiza data/clubs.json CONSERVANDO todos los datos manuales ya introducidos.

Ligas incluidas:
  La Liga, Premier League, Bundesliga, Serie A, Ligue 1, Eredivisie, Primeira Liga

Cómo ejecutarlo manualmente:
  pip install requests
  python scripts/fetch_clubs.py
"""

import requests
import json
import os
from datetime import datetime, timezone

OUTPUT_FILE = "data/clubs.json"
BASE_URL    = "https://www.thesportsdb.com/api/v1/json/1"

LEAGUES = {
    "La Liga":         "Spanish La Liga",
    "Premier League":  "English Premier League",
    "Bundesliga":      "German Bundesliga",
    "Serie A":         "Italian Serie A",
    "Ligue 1":         "French Ligue 1",
    "Eredivisie":      "Dutch Eredivisie",
    "Primeira Liga":   "Portuguese Primeira Liga",
}

MANUAL_FIELDS = [
    "ticketing_provider","has_own_app","resale_channels",
    "price_range_eur","ticket_url","fever_status","notes",
]

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def now_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def load_existing(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # índice por nombre (la API no devuelve el mismo ID numérico siempre)
        return {c["name"]: c for c in data.get("clubs", [])}
    return {}

def fetch_teams(league_api_name):
    url = f"{BASE_URL}/search_all_teams.php?l={requests.utils.quote(league_api_name)}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json().get("teams") or []
    except Exception as e:
        print(f"  ⚠️  Error en '{league_api_name}': {e}")
        return []

def build_club(team, league_name, existing):
    name = team.get("strTeam", "")
    prev = existing.get(name, {})
    return {
        "id":               team.get("idTeam", ""),
        "name":             name,
        "short_name":       team.get("strTeamShort", ""),
        "logo_url":         team.get("strTeamBadge", ""),
        "league":           league_name,
        "country":          team.get("strCountry", ""),
        "founded":          team.get("intFormedYear", ""),
        "stadium":          team.get("strStadium", ""),
        "capacity":         _to_int(team.get("intStadiumCapacity")),
        "stadium_location": team.get("strStadiumLocation", ""),
        # Campos manuales: se conservan si ya existían
        "ticketing_provider": prev.get("ticketing_provider", ""),
        "has_own_app":        prev.get("has_own_app", None),
        "resale_channels":    prev.get("resale_channels", []),
        "price_range_eur":    prev.get("price_range_eur", []),
        "ticket_url":         prev.get("ticket_url", team.get("strWebsite", "")),
        "fever_status":       prev.get("fever_status", "prospect"),
        "notes":              prev.get("notes", ""),
        "last_updated":       now_date(),
    }

def _to_int(v):
    try: return int(v)
    except: return None

def main():
    print("🔄  Actualizando clubs.json…\n")
    existing = load_existing(OUTPUT_FILE)
    clubs = []

    for league_name, league_api in LEAGUES.items():
        print(f"  📥  {league_name}…")
        teams = fetch_teams(league_api)
        print(f"      → {len(teams)} equipos")
        for team in teams:
            clubs.append(build_club(team, league_name, existing))

    clubs.sort(key=lambda c: (c["league"], c["name"]))

    output = {
        "meta": {
            "description": "Football Ticketing Intelligence — Fever",
            "last_updated": now_iso(),
            "total_clubs":  len(clubs),
            "leagues":      list(LEAGUES.keys()),
        },
        "clubs": clubs,
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅  {len(clubs)} clubs guardados en '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()
