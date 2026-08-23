# Premier League 2026-27 Tracker

A simple static tracker for the Premier League, with three tabs:
- **League Table**: full standings, color-coded by European qualification zone (Champions League, Europa League, Conference League) and relegation zone, plus a "European Race" view of the top 8 and a "Relegation Watch" view of what each bottom-table team needs to reach safety.
- **Club Stats**: clean sheets, home/away form splits, biggest wins & heaviest losses — all derived from match results.
- **Player Stats**: Golden Boot race, plus expandable lists for Most Goals, Most Assists, Most Goals & Assists, Most Yellow Cards, Most Red Cards, and Most Clean Sheets (goalkeepers).

## Data sources
- [football-data.org](https://www.football-data.org/) free API (Premier League competition code `PL`) — standings, matches, goals/penalties.
- The Premier League's own public stats API (`sdp-prem-prod.premier-league-prod.pulselive.com`) — assists, yellow cards, red cards, and goalkeeper clean sheets. No API key required for this one; it's the same backend premierleague.com's own stats pages call.

## Regenerating

```bash
export FOOTBALL_DATA_API_TOKEN=your_token_here
./fetch_data.sh
git add index.html
git commit -m "Refresh standings"
git push
```

Not live-updating — rebuild after each gameweek (or whenever) to refresh the table.
