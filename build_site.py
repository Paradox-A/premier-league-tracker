import json
import os
from datetime import datetime, timezone

API_TOKEN = os.environ.get("FOOTBALL_DATA_API_TOKEN")
STANDINGS_PATH = "standings.json"
OUT_PATH = "index.html"

SAFETY_THRESHOLD = 38  # rough historical PL survival benchmark (points)
TOTAL_GAMES = 38

d = json.load(open(STANDINGS_PATH))
table = d["standings"][0]["table"]
season = d["season"]
matchday = season["currentMatchday"]

# Sort defensively by position (API already sorts, but ties can share position numbers)
table = sorted(table, key=lambda t: (t["position"], -t["points"], -t["goalDifference"]))

def zone_for(pos):
    if pos <= 4:
        return ("cl", "Champions League")
    if pos == 5:
        return ("el", "Europa League")
    if pos == 6:
        return ("ecl", "Conference League")
    if pos >= 18:
        return ("rel", "Relegation")
    return ("", "")

rows_html = []
for t in table:
    pos = t["position"]
    zone_class, zone_label = zone_for(pos)
    played = t["playedGames"]
    remaining = TOTAL_GAMES - played
    pts = t["points"]
    gd = t["goalDifference"]
    gd_str = f"+{gd}" if gd > 0 else str(gd)
    form = t.get("form") or "—"
    rows_html.append(f"""
    <tr class="{zone_class}">
      <td class="pos">{pos}</td>
      <td class="team"><img src="{t['team']['crest']}" alt="" class="crest"> {t['team']['shortName']}</td>
      <td>{played}</td>
      <td>{t['won']}</td>
      <td>{t['draw']}</td>
      <td>{t['lost']}</td>
      <td>{t['goalsFor']}</td>
      <td>{t['goalsAgainst']}</td>
      <td>{gd_str}</td>
      <td class="pts">{pts}</td>
      <td class="form">{form}</td>
    </tr>""")

# European race: positions 1-8 (top 4 + EL/ECL + closest chasers)
euro_zone = [t for t in table if t["position"] <= 8]
euro_rows = []
for t in euro_zone:
    pos = t["position"]
    zone_class, zone_label = zone_for(pos)
    label = zone_label if zone_label else "Chasing pack"
    played = t["playedGames"]
    remaining = TOTAL_GAMES - played
    pts_needed_vs_4th = None
    fourth = table[3]["points"]
    gap = fourth - t["points"]
    euro_rows.append(f"""
    <tr class="{zone_class}">
      <td class="pos">{pos}</td>
      <td class="team"><img src="{t['team']['crest']}" alt="" class="crest"> {t['team']['shortName']}</td>
      <td>{label}</td>
      <td>{t['points']}</td>
      <td>{remaining}</td>
      <td>{'—' if pos <= 4 else (f'{gap} pt behind 4th' if gap > 0 else 'Level with 4th')}</td>
    </tr>""")

# Relegation watch: bottom 6 (relegation zone + closest above)
rel_zone = sorted(table, key=lambda t: t["position"])[-6:]
rel_rows = []
safe_line_team = None
for t in table:
    if t["position"] == 17:
        safe_line_team = t
for t in rel_zone:
    pos = t["position"]
    played = t["playedGames"]
    remaining = TOTAL_GAMES - played
    pts = t["points"]
    pts_needed = max(SAFETY_THRESHOLD - pts, 0)
    ppg_needed = (pts_needed / remaining) if remaining > 0 else float('inf')
    if remaining == 0 and pts < SAFETY_THRESHOLD:
        verdict = "Relegated (out of games)"
    elif ppg_needed <= 0:
        verdict = "Already past safety benchmark"
    elif ppg_needed <= 1.0:
        verdict = f"Needs {pts_needed} pts from {remaining} games ({ppg_needed:.2f} pts/game pace)"
    elif ppg_needed <= 1.8:
        verdict = f"Needs {pts_needed} pts from {remaining} games ({ppg_needed:.2f} pts/game — above current league-average pace)"
    else:
        verdict = f"Needs {pts_needed} pts from {remaining} games ({ppg_needed:.2f} pts/game — very steep, likely needs a big turnaround)"
    zone_class, _ = zone_for(pos)
    rel_rows.append(f"""
    <tr class="{zone_class}">
      <td class="pos">{pos}</td>
      <td class="team"><img src="{t['team']['crest']}" alt="" class="crest"> {t['team']['shortName']}</td>
      <td>{pts}</td>
      <td>{remaining}</td>
      <td>{verdict}</td>
    </tr>""")

updated = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Premier League 2026-27 Tracker</title>
<style>
  :root {{
    --bg: #f6f1e7;
    --card: #ffffff;
    --text: #1a1a1a;
    --muted: #6b6b6b;
    --border: #e2ddd0;
    --cl: #d6f5d6;
    --cl-text: #1a6b1a;
    --el: #d6e8ff;
    --el-text: #1a4a8a;
    --ecl: #e0d6ff;
    --ecl-text: #4a1a8a;
    --rel: #ffd6d6;
    --rel-text: #8a1a1a;
    --accent: #37003c;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #16131a;
      --card: #211d29;
      --text: #f0ede4;
      --muted: #a39d8f;
      --border: #3a3444;
      --cl: #143d14;
      --cl-text: #8fe08f;
      --el: #143355;
      --el-text: #9cc4f5;
      --ecl: #2e1a55;
      --ecl-text: #c9b3f5;
      --rel: #551a1a;
      --rel-text: #f5a3a3;
      --accent: #b494ff;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #16131a;
    --card: #211d29;
    --text: #f0ede4;
    --muted: #a39d8f;
    --border: #3a3444;
    --cl: #143d14;
    --cl-text: #8fe08f;
    --el: #143355;
    --el-text: #9cc4f5;
    --ecl: #2e1a55;
    --ecl-text: #c9b3f5;
    --rel: #551a1a;
    --rel-text: #f5a3a3;
    --accent: #b494ff;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    padding: 24px 16px 60px;
  }}
  .wrap {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; color: var(--accent); }}
  .updated {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
    overflow-x: auto;
  }}
  h2 {{ font-size: 1.1rem; margin-top: 0; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; white-space: nowrap; }}
  th, td {{ padding: 6px 8px; text-align: center; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
  td.team, th.team {{ text-align: left; }}
  .crest {{ width: 16px; height: 16px; vertical-align: middle; margin-right: 6px; }}
  .pos {{ font-weight: 700; }}
  .pts {{ font-weight: 700; }}
  tr.cl {{ background: var(--cl); color: var(--cl-text); }}
  tr.el {{ background: var(--el); color: var(--el-text); }}
  tr.ecl {{ background: var(--ecl); color: var(--ecl-text); }}
  tr.rel {{ background: var(--rel); color: var(--rel-text); }}
  .legend {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: 0.78rem; margin-top: 10px; color: var(--muted); }}
  .legend span {{ display: inline-flex; align-items: center; gap: 5px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}
  .dot.cl {{ background: var(--cl); }}
  .dot.el {{ background: var(--el); }}
  .dot.ecl {{ background: var(--ecl); }}
  .dot.rel {{ background: var(--rel); }}
  .note {{ color: var(--muted); font-size: 0.8rem; margin-top: 8px; }}
  footer {{ text-align: center; color: var(--muted); font-size: 0.75rem; margin-top: 30px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Premier League 2026-27 Tracker</h1>
  <div class="updated">Matchday {matchday} · Last updated {updated}</div>

  <div class="card">
    <h2>League Table</h2>
    <table>
      <thead>
        <tr>
          <th>#</th><th class="team">Team</th><th>P</th><th>W</th><th>D</th><th>L</th>
          <th>GF</th><th>GA</th><th>GD</th><th>Pts</th><th>Form</th>
        </tr>
      </thead>
      <tbody>{"".join(rows_html)}
      </tbody>
    </table>
    <div class="legend">
      <span><span class="dot cl"></span>Champions League (1-4)</span>
      <span><span class="dot el"></span>Europa League (5)</span>
      <span><span class="dot ecl"></span>Conference League (6)</span>
      <span><span class="dot rel"></span>Relegation (18-20)</span>
    </div>
    <div class="note">European qualification spots can shift based on cup-competition winners (FA Cup, League Cup) already qualifying via league position — actual allocations are confirmed toward the end of the season.</div>
  </div>

  <div class="card">
    <h2>European Race</h2>
    <table>
      <thead><tr><th>#</th><th class="team">Team</th><th>Zone</th><th>Pts</th><th>Games Left</th><th>Gap to 4th</th></tr></thead>
      <tbody>{"".join(euro_rows)}</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Relegation Watch</h2>
    <table>
      <thead><tr><th>#</th><th class="team">Team</th><th>Pts</th><th>Games Left</th><th>What it takes to stay up</th></tr></thead>
      <tbody>{"".join(rel_rows)}</tbody>
    </table>
    <div class="note">"Safety" modeled as ~{SAFETY_THRESHOLD} points, a rough historical Premier League survival benchmark — the real cutoff varies year to year based on how bad the bottom teams are.</div>
  </div>

  <footer>Data: football-data.org · Rebuilt periodically, not live-updating</footer>
</div>
</body>
</html>
"""

with open(OUT_PATH, "w") as f:
    f.write(html)
print("wrote", OUT_PATH, len(html), "bytes")
