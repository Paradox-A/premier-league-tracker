import json
import os
from datetime import datetime, timezone
from collections import defaultdict

API_TOKEN = os.environ.get("FOOTBALL_DATA_API_TOKEN")
STANDINGS_PATH = "standings.json"
MATCHES_PATH = "matches.json"
SCORERS_PATH = "scorers.json"
OUT_PATH = "index.html"

SAFETY_THRESHOLD = 38
TOTAL_GAMES = 38

standings_data = json.load(open(STANDINGS_PATH))
table = standings_data["standings"][0]["table"]
season = standings_data["season"]
matchday = season["currentMatchday"]
table = sorted(table, key=lambda t: (t["position"], -t["points"], -t["goalDifference"]))

matches_data = json.load(open(MATCHES_PATH))
finished = [m for m in matches_data["matches"] if m["status"] == "FINISHED"]

scorers_data = json.load(open(SCORERS_PATH))
scorers = scorers_data["scorers"]

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

# ---------- League table rows ----------
rows_html = []
for t in table:
    pos = t["position"]
    zone_class, _ = zone_for(pos)
    played = t["playedGames"]
    pts = t["points"]
    gd = t["goalDifference"]
    gd_str = f"+{gd}" if gd > 0 else str(gd)
    form = t.get("form") or "—"
    rows_html.append(f"""
    <tr class="{zone_class}">
      <td class="pos">{pos}</td>
      <td class="team"><img src="{t['team']['crest']}" alt="" class="crest"> {t['team']['shortName']}</td>
      <td>{played}</td><td>{t['won']}</td><td>{t['draw']}</td><td>{t['lost']}</td>
      <td>{t['goalsFor']}</td><td>{t['goalsAgainst']}</td><td>{gd_str}</td>
      <td class="pts">{pts}</td><td class="form">{form}</td>
    </tr>""")

euro_zone = [t for t in table if t["position"] <= 8]
euro_rows = []
fourth = table[3]["points"]
for t in euro_zone:
    pos = t["position"]
    zone_class, zone_label = zone_for(pos)
    label = zone_label if zone_label else "Chasing pack"
    remaining = TOTAL_GAMES - t["playedGames"]
    gap = fourth - t["points"]
    euro_rows.append(f"""
    <tr class="{zone_class}">
      <td class="pos">{pos}</td>
      <td class="team"><img src="{t['team']['crest']}" alt="" class="crest"> {t['team']['shortName']}</td>
      <td>{label}</td><td>{t['points']}</td><td>{remaining}</td>
      <td>{'—' if pos <= 4 else (f'{gap} pt behind 4th' if gap > 0 else 'Level with 4th')}</td>
    </tr>""")

rel_zone = sorted(table, key=lambda t: t["position"])[-6:]
rel_rows = []
for t in rel_zone:
    pos = t["position"]
    remaining = TOTAL_GAMES - t["playedGames"]
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
        verdict = f"Needs {pts_needed} pts from {remaining} games ({ppg_needed:.2f} pts/game — above league-average pace)"
    else:
        verdict = f"Needs {pts_needed} pts from {remaining} games ({ppg_needed:.2f} pts/game — steep, needs a big turnaround)"
    zone_class, _ = zone_for(pos)
    rel_rows.append(f"""
    <tr class="{zone_class}">
      <td class="pos">{pos}</td>
      <td class="team"><img src="{t['team']['crest']}" alt="" class="crest"> {t['team']['shortName']}</td>
      <td>{pts}</td><td>{remaining}</td><td>{verdict}</td>
    </tr>""")

# ---------- Club stats derived from finished matches ----------
club = defaultdict(lambda: {
    "name": None, "crest": None, "gf": 0, "ga": 0, "clean_sheets": 0, "failed_to_score": 0,
    "home_pts": 0, "home_played": 0, "away_pts": 0, "away_played": 0,
    "results": [],  # chronological list of 'W'/'D'/'L'
    "biggest_win": None, "heaviest_loss": None,
})

finished_sorted = sorted(finished, key=lambda m: m["utcDate"])
for m in finished_sorted:
    home = m["homeTeam"]; away = m["awayTeam"]
    hs = m["score"]["fullTime"]["home"]; as_ = m["score"]["fullTime"]["away"]
    for side, opp_side, gf, ga, is_home in [(home, away, hs, as_, True), (away, home, as_, hs, False)]:
        c = club[side["id"]]
        c["name"] = side["shortName"]; c["crest"] = side["crest"]
        c["gf"] += gf; c["ga"] += ga
        if ga == 0:
            c["clean_sheets"] += 1
        if gf == 0:
            c["failed_to_score"] += 1
        margin = gf - ga
        result = "W" if margin > 0 else ("D" if margin == 0 else "L")
        c["results"].append(result)
        pts = 3 if result == "W" else (1 if result == "D" else 0)
        if is_home:
            c["home_pts"] += pts; c["home_played"] += 1
        else:
            c["away_pts"] += pts; c["away_played"] += 1
        if result == "W":
            if c["biggest_win"] is None or margin > c["biggest_win"][0]:
                c["biggest_win"] = (margin, f"{gf}-{ga} vs {opp_side['shortName']}")
        if result == "L":
            deficit = ga - gf
            if c["heaviest_loss"] is None or deficit > c["heaviest_loss"][0]:
                c["heaviest_loss"] = (deficit, f"{gf}-{ga} vs {opp_side['shortName']}")

clean_sheet_rows = []
for cid, c in sorted(club.items(), key=lambda kv: (-kv[1]["clean_sheets"], kv[1]["ga"])):
    played = len(c["results"])
    if played == 0:
        continue
    clean_sheet_rows.append(f"""
    <tr>
      <td class="team"><img src="{c['crest']}" alt="" class="crest"> {c['name']}</td>
      <td>{played}</td><td>{c['clean_sheets']}</td>
      <td>{c['ga']/played:.2f}</td><td>{c['failed_to_score']}</td>
    </tr>""")

form_home_away_rows = []
for cid, c in sorted(club.items(), key=lambda kv: -( (kv[1]["home_pts"]+kv[1]["away_pts"]) )):
    played = len(c["results"])
    if played == 0:
        continue
    last5 = "".join(c["results"][-5:])
    home_ppg = (c["home_pts"]/c["home_played"]) if c["home_played"] else 0
    away_ppg = (c["away_pts"]/c["away_played"]) if c["away_played"] else 0
    form_home_away_rows.append(f"""
    <tr>
      <td class="team"><img src="{c['crest']}" alt="" class="crest"> {c['name']}</td>
      <td>{last5 or '—'}</td>
      <td>{c['home_pts']}pts / {c['home_played']}g ({home_ppg:.2f}/g)</td>
      <td>{c['away_pts']}pts / {c['away_played']}g ({away_ppg:.2f}/g)</td>
    </tr>""")

biggest_wins = sorted([ (c["biggest_win"][0], c["name"], c["biggest_win"][1]) for c in club.values() if c["biggest_win"]], reverse=True)[:5]
heaviest_losses = sorted([ (c["heaviest_loss"][0], c["name"], c["heaviest_loss"][1]) for c in club.values() if c["heaviest_loss"]], reverse=True)[:5]
biggest_win_rows = "".join(f"<tr><td>{name}</td><td>{detail}</td></tr>" for _, name, detail in biggest_wins) or "<tr><td colspan='2'>Not enough results yet</td></tr>"
heaviest_loss_rows = "".join(f"<tr><td>{name}</td><td>{detail}</td></tr>" for _, name, detail in heaviest_losses) or "<tr><td colspan='2'>Not enough results yet</td></tr>"

# ---------- Player stats from scorers ----------
def player_row(s, highlight_field):
    goals = s.get("goals") or 0
    assists_raw = s.get("assists")
    assists = assists_raw or 0
    pens_raw = s.get("penalties")
    pens = pens_raw or 0
    played = s.get("playedMatches") or 0
    involvements = goals + assists
    per_game = (goals/played) if played else 0
    cls = lambda f: "pts" if f == highlight_field else ""
    return f"""
    <tr>
      <td class="team"><img src="{s['team']['crest']}" alt="" class="crest"> {s['player']['name']}</td>
      <td>{s['team']['shortName']}</td>
      <td>{played}</td>
      <td class="{cls('goals')}">{goals}</td>
      <td class="{cls('assists')}">{assists if assists_raw is not None else '—'}</td>
      <td class="{cls('inv')}">{involvements}</td>
      <td>{pens if pens_raw is not None else '—'}</td>
      <td>{per_game:.2f}</td>
    </tr>"""

by_goals = sorted(scorers, key=lambda s: (-(s.get("goals") or 0), -(s.get("assists") or 0)))
by_assists = sorted(scorers, key=lambda s: (-(s.get("assists") or 0), -(s.get("goals") or 0)))
by_involvements = sorted(scorers, key=lambda s: (-((s.get("goals") or 0) + (s.get("assists") or 0))))

any_real_assists = any(s.get("assists") is not None for s in scorers)
assists_data_note = "" if any_real_assists else """<div class="note">⚠ The data source hasn't started tracking assists yet this early in the season — every player currently shows "assists: none," so this list is really just sorted by goals as a fallback. It'll reflect real assist counts once the data catches up.</div>"""

goals_rows = "".join(player_row(s, "goals") for s in by_goals)
assists_rows = "".join(player_row(s, "assists") for s in by_assists)
involvements_rows = "".join(player_row(s, "inv") for s in by_involvements)

PLAYER_TABLE_HEAD = """<thead><tr><th class="team">Player</th><th>Club</th><th>Games</th><th>Goals</th><th>Assists</th><th>Goal Inv.</th><th>Pens</th><th>Goals/Game</th></tr></thead>"""

updated = datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M UTC")

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Premier League 2026-27 Tracker</title>
<style>
  :root {{
    --bg: #f6f1e7; --card: #ffffff; --text: #1a1a1a; --muted: #6b6b6b; --border: #e2ddd0;
    --cl: #d6f5d6; --cl-text: #1a6b1a; --el: #d6e8ff; --el-text: #1a4a8a;
    --ecl: #e0d6ff; --ecl-text: #4a1a8a; --rel: #ffd6d6; --rel-text: #8a1a1a;
    --accent: #37003c; --tab-bg: #eee6d6; --tab-active: #37003c; --tab-active-text: #ffffff;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #16131a; --card: #211d29; --text: #f0ede4; --muted: #a39d8f; --border: #3a3444;
      --cl: #143d14; --cl-text: #8fe08f; --el: #143355; --el-text: #9cc4f5;
      --ecl: #2e1a55; --ecl-text: #c9b3f5; --rel: #551a1a; --rel-text: #f5a3a3;
      --accent: #b494ff; --tab-bg: #2a2534; --tab-active: #b494ff; --tab-active-text: #16131a;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #16131a; --card: #211d29; --text: #f0ede4; --muted: #a39d8f; --border: #3a3444;
    --cl: #143d14; --cl-text: #8fe08f; --el: #143355; --el-text: #9cc4f5;
    --ecl: #2e1a55; --ecl-text: #c9b3f5; --rel: #551a1a; --rel-text: #f5a3a3;
    --accent: #b494ff; --tab-bg: #2a2534; --tab-active: #b494ff; --tab-active-text: #16131a;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 24px 16px 60px; }}
  .wrap {{ max-width: 940px; margin: 0 auto; }}
  h1 {{ font-size: 1.6rem; margin-bottom: 4px; color: var(--accent); }}
  .updated {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 18px; }}
  .tabs {{ display: flex; gap: 6px; margin-bottom: 20px; flex-wrap: wrap; }}
  .tab-btn {{
    background: var(--tab-bg); color: var(--text); border: none; border-radius: 8px;
    padding: 10px 16px; font-size: 0.9rem; font-weight: 600; cursor: pointer;
  }}
  .tab-btn.active {{ background: var(--tab-active); color: var(--tab-active-text); }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 20px; overflow-x: auto; }}
  h2 {{ font-size: 1.1rem; margin-top: 0; }}
  .intro {{ font-size: 0.88rem; color: var(--muted); margin-bottom: 16px; line-height: 1.5; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; white-space: nowrap; }}
  th, td {{ padding: 6px 8px; text-align: center; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; font-size: 0.72rem; text-transform: uppercase; }}
  td.team, th.team {{ text-align: left; }}
  .crest {{ width: 16px; height: 16px; vertical-align: middle; margin-right: 6px; }}
  .pos {{ font-weight: 700; }} .pts {{ font-weight: 700; }}
  tr.cl {{ background: var(--cl); color: var(--cl-text); }}
  tr.el {{ background: var(--el); color: var(--el-text); }}
  tr.ecl {{ background: var(--ecl); color: var(--ecl-text); }}
  tr.rel {{ background: var(--rel); color: var(--rel-text); }}
  .legend {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: 0.78rem; margin-top: 10px; color: var(--muted); }}
  .legend span {{ display: inline-flex; align-items: center; gap: 5px; }}
  .dot {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}
  .dot.cl {{ background: var(--cl); }} .dot.el {{ background: var(--el); }}
  .dot.ecl {{ background: var(--ecl); }} .dot.rel {{ background: var(--rel); }}
  .note {{ color: var(--muted); font-size: 0.8rem; margin-top: 8px; }}
  .explainer {{ background: var(--tab-bg); border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: var(--text); margin-bottom: 12px; line-height: 1.5; }}
  .explainer b {{ color: var(--accent); }}
  footer {{ text-align: center; color: var(--muted); font-size: 0.75rem; margin-top: 30px; }}
  details.stat-accordion {{ border: 1px solid var(--border); border-radius: 10px; margin-bottom: 12px; overflow: hidden; }}
  details.stat-accordion summary {{
    cursor: pointer; padding: 14px 16px; font-weight: 700; font-size: 0.98rem;
    list-style: none; display: flex; justify-content: space-between; align-items: center;
    background: var(--card);
  }}
  details.stat-accordion summary::-webkit-details-marker {{ display: none; }}
  details.stat-accordion summary::after {{ content: "+"; font-size: 1.2rem; color: var(--muted); }}
  details.stat-accordion[open] summary::after {{ content: "−"; }}
  details.stat-accordion summary .sub {{ font-weight: 400; font-size: 0.78rem; color: var(--muted); margin-top: 2px; display: block; }}
  details.stat-accordion .accordion-body {{ padding: 0 16px 16px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Premier League 2026-27 Tracker</h1>
  <div class="updated">Matchday {matchday} · Last updated {updated}</div>

  <div class="tabs">
    <button class="tab-btn active" onclick="showTab('table')">League Table</button>
    <button class="tab-btn" onclick="showTab('club')">Club Stats</button>
    <button class="tab-btn" onclick="showTab('player')">Player Stats</button>
  </div>

  <div id="tab-table" class="tab-panel active">
    <div class="card">
      <h2>League Table</h2>
      <table>
        <thead><tr><th>#</th><th class="team">Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th><th>Form</th></tr></thead>
        <tbody>{"".join(rows_html)}</tbody>
      </table>
      <div class="legend">
        <span><span class="dot cl"></span>Champions League (1-4)</span>
        <span><span class="dot el"></span>Europa League (5)</span>
        <span><span class="dot ecl"></span>Conference League (6)</span>
        <span><span class="dot rel"></span>Relegation (18-20)</span>
      </div>
      <div class="note">European qualification spots can shift based on cup-competition winners already qualifying via league position — actual allocations confirm toward season's end.</div>
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
      <div class="note">"Safety" modeled as ~{SAFETY_THRESHOLD} points, a rough historical Premier League survival benchmark.</div>
    </div>
  </div>

  <div id="tab-club" class="tab-panel">
    <div class="explainer">
      <b>New to the Premier League?</b> The table tells you <i>where</i> a team stands, but not <i>how</i> they got there. These stats show the underlying strengths and weaknesses — a team can have a good record while quietly being fragile defensively, or vice versa.
    </div>

    <div class="card">
      <h2>Defensive Strength: Clean Sheets</h2>
      <div class="explainer">A <b>clean sheet</b> is a game where a team doesn't concede at all. It's the single clearest sign of defensive solidity — teams that win titles almost always lead the league in clean sheets, because you can't lose a game you don't concede in.</div>
      <table>
        <thead><tr><th class="team">Team</th><th>Played</th><th>Clean Sheets</th><th>Goals Conceded / Game</th><th>Failed to Score</th></tr></thead>
        <tbody>{"".join(clean_sheet_rows) or "<tr><td colspan=5>No finished matches yet</td></tr>"}</tbody>
      </table>
      <div class="note"><b>Failed to Score</b> counts games where a team didn't score at all — a blunt but telling sign of attacking struggles.</div>
    </div>

    <div class="card">
      <h2>Home Fortress vs. Road Warriors</h2>
      <div class="explainer">Some teams are much stronger at home than away (or the reverse) — this is one of the oldest storylines in football. <b>Points per game (PPG)</b> at home vs. away shows exactly how lopsided that split is. <b>Form</b> is the last 5 results (most recent last) — a better read on momentum than the season-long record.</div>
      <table>
        <thead><tr><th class="team">Team</th><th>Form (last 5)</th><th>Home Record</th><th>Away Record</th></tr></thead>
        <tbody>{"".join(form_home_away_rows) or "<tr><td colspan=4>No finished matches yet</td></tr>"}</tbody>
      </table>
    </div>

    <div class="card">
      <h2>Biggest Wins &amp; Heaviest Losses</h2>
      <div class="explainer">Goal margin matters beyond the 3 points — a big win boosts goal difference (which breaks ties in the table) and can be a statement result against a rival.</div>
      <div style="display:flex; gap:16px; flex-wrap:wrap;">
        <table style="flex:1; min-width:220px;">
          <thead><tr><th class="team">Team</th><th>Biggest Win</th></tr></thead>
          <tbody>{biggest_win_rows}</tbody>
        </table>
        <table style="flex:1; min-width:220px;">
          <thead><tr><th class="team">Team</th><th>Heaviest Loss</th></tr></thead>
          <tbody>{heaviest_loss_rows}</tbody>
        </table>
      </div>
    </div>

    <div class="note" style="margin-top: -8px;">Not shown: possession, shots, passing accuracy, tackles, or expected goals (xG) — these require a paid data source. Everything above is derived directly from final match scores.</div>
  </div>

  <div id="tab-player" class="tab-panel">
    <div class="explainer">
      <b>New to the Premier League?</b> The <b>Golden Boot</b> (top scorer) is the most prestigious individual award in English football outside of Player of the Season. But goals alone don't capture everything a player contributes — this table adds context.
    </div>
    <div class="card">
      <h2>Golden Boot Race &amp; Goal Involvements</h2>
      <div class="explainer">
        <b>Goals</b>: the headline number, and what decides the Golden Boot.<br>
        <b>Assists</b>: the pass that directly leads to a goal — a measure of creativity, not just finishing.<br>
        <b>Goal Involvements</b> (goals + assists): a fuller picture of a player's attacking output — a player with 8 goals and 10 assists is arguably more valuable than one with 12 goals and 0 assists.<br>
        <b>Goals/Game</b>: raw totals favor players who've played more games — this rate stat levels the comparison.<br>
        <b>Penalties</b>: shown separately since penalty goals are viewed differently from open-play goals (some fans discount them when judging a striker's true quality).
      </div>
      <table>{PLAYER_TABLE_HEAD}<tbody>{goals_rows or "<tr><td colspan=8>No scorer data yet</td></tr>"}</tbody></table>
      <div class="note">Not shown: shots, expected goals (xG), key passes, dribbles, tackles, or cards — the free data source used here only tracks goals, assists, penalties, and appearances. Deeper stats (like xG) require a paid provider.</div>
    </div>

    <div class="explainer" style="margin-top: 4px;">
      <b>Want just one ranking at a time?</b> The sections below break the same data out individually, sorted by each specific stat.
    </div>

    <details class="stat-accordion">
      <summary>Most Goals <span class="sub">The Golden Boot race — decided by goals alone, nothing else</span></summary>
      <div class="accordion-body">
        <div class="explainer"><b>Goals</b> is the headline number and what the actual Golden Boot award is decided by. It's the most-watched individual stat in the league, but it rewards finishers over creators — see "Most Goals & Assists" below for the fuller picture.</div>
        <table>{PLAYER_TABLE_HEAD}<tbody>{goals_rows or "<tr><td colspan=8>No scorer data yet</td></tr>"}</tbody></table>
      </div>
    </details>

    <details class="stat-accordion">
      <summary>Most Assists <span class="sub">Who's creating goals for others, not just scoring them</span></summary>
      <div class="accordion-body">
        <div class="explainer"><b>Assists</b> credit the pass (or occasionally the touch) that directly leads to a goal. It's the clearest single measure of creativity — a player can be hugely valuable to a team's attack without scoring much themselves.</div>
        {assists_data_note}
        <table>{PLAYER_TABLE_HEAD}<tbody>{assists_rows or "<tr><td colspan=8>No assist data yet</td></tr>"}</tbody></table>
      </div>
    </details>

    <details class="stat-accordion">
      <summary>Most Goals &amp; Assists <span class="sub">Total attacking output — often a better "who's actually best" ranking than goals alone</span></summary>
      <div class="accordion-body">
        <div class="explainer"><b>Goal Involvements</b> (goals + assists) gives a fuller picture of a player's attacking output than the Golden Boot table does on its own. A player with 8 goals and 10 assists has been directly involved in 18 goals — arguably more valuable to their team than someone with 12 goals and 0 assists, even though the latter would top the pure scoring chart.</div>
        <table>{PLAYER_TABLE_HEAD}<tbody>{involvements_rows or "<tr><td colspan=8>No data yet</td></tr>"}</tbody></table>
      </div>
    </details>

    <div class="note">Also shown in each table: <b>Penalties</b> (shown separately since penalty goals are viewed differently from open-play ones), and <b>Goals/Game</b> (a rate stat, since raw totals favor players who've played more games). Not shown: shots, expected goals (xG), key passes, dribbles, tackles, or cards — the free data source used here only tracks goals, assists, penalties, and appearances.</div>
  </div>

  <footer>Data: football-data.org · Rebuilt periodically, not live-updating</footer>
</div>
<script>
function showTab(name) {{
  document.querySelectorAll('.tab-panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}}
</script>
</body>
</html>
"""

with open(OUT_PATH, "w") as f:
    f.write(html)
print("wrote", OUT_PATH, len(html), "bytes")
