#!/bin/bash
# Requires FOOTBALL_DATA_API_TOKEN env var set (free key from football-data.org)
set -e
curl -s -H "X-Auth-Token: $FOOTBALL_DATA_API_TOKEN" "https://api.football-data.org/v4/competitions/PL/standings" -o standings.json
curl -s -H "X-Auth-Token: $FOOTBALL_DATA_API_TOKEN" "https://api.football-data.org/v4/competitions/PL/matches" -o matches.json
curl -s -H "X-Auth-Token: $FOOTBALL_DATA_API_TOKEN" "https://api.football-data.org/v4/competitions/PL/scorers?limit=50" -o scorers.json

# Premier League's own public stats API — no auth token needed
curl -s "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=goal_assists%3Adesc&country=&_limit=15" -o pl_assists.json
curl -s "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=yellow_cards%3Adesc&country=&_limit=15" -o pl_yellow_cards.json
curl -s "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=total_red_cards%3Adesc&country=&_limit=15" -o pl_red_cards.json
curl -s "https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v3/competitions/8/seasons/2026/players/stats/leaderboard?_sort=clean_sheets%3Adesc&country=&_limit=60" -o pl_clean_sheets.json

python3 build_site.py
echo "Rebuilt site/index.html"
