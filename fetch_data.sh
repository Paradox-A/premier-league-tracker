#!/bin/bash
# Requires FOOTBALL_DATA_API_TOKEN env var set (free key from football-data.org)
set -e

fetch() {
  # $1 = output file, rest = curl args (URL, headers, etc.)
  local out="$1"; shift
  curl -s "$@" -o "$out"
  if grep -q '"errorCode"' "$out" 2>/dev/null; then
    echo "ERROR: fetch failed for $out — $(cat "$out")" >&2
    exit 1
  fi
  sleep 7
}

fetch standings.json -H "X-Auth-Token: $FOOTBALL_DATA_API_TOKEN" "https://api.football-data.org/v4/competitions/PL/standings"
fetch matches.json -H "X-Auth-Token: $FOOTBALL_DATA_API_TOKEN" "https://api.football-data.org/v4/competitions/PL/matches"
fetch scorers.json -H "X-Auth-Token: $FOOTBALL_DATA_API_TOKEN" "https://api.football-data.org/v4/competitions/PL/scorers?limit=50"

# Premier League's own public stats API — no auth token needed
fetch pl_assists.json "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=goal_assists%3Adesc&country=&_limit=15"
fetch pl_yellow_cards.json "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=yellow_cards%3Adesc&country=&_limit=15"
fetch pl_red_cards.json "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=total_red_cards%3Adesc&country=&_limit=15"
fetch pl_clean_sheets.json "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=clean_sheets%3Adesc&country=&_limit=60"

python3 build_site.py
echo "Rebuilt site/index.html"
