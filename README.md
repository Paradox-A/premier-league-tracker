# Premier League 2026-27 Tracker

A simple static tracker for the Premier League table, with:
- Full standings, color-coded by European qualification zone (Champions League, Europa League, Conference League) and relegation zone
- A "European Race" view of the top 8 and how far they are from the Champions League cutoff
- A "Relegation Watch" view showing what each bottom-table team needs (points from remaining games) to reach a rough safety benchmark

## Data source
[football-data.org](https://www.football-data.org/) free API (Premier League competition code `PL`).

## Regenerating

```bash
export FOOTBALL_DATA_API_TOKEN=your_token_here
./fetch_data.sh
git add index.html
git commit -m "Refresh standings"
git push
```

Not live-updating — rebuild after each gameweek (or whenever) to refresh the table.
