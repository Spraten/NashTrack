# NashTrack

NashTrack is a compact sports command center built for an 800x480 Raspberry Pi touchscreen. The app runs as a local Vite web UI from `main.py`, opens in a kiosk-style browser window, and keeps a Kivy fallback available with `--kivy`.

## Current Status

- [x] Compact 800x480 dashboard with sidebar, topbar, footer, favorites, calendar, headlines, and upcoming events.
- [x] Web launcher flow through `main.py` and `app/web_launcher.py`.
- [x] Raspberry Pi Chromium fullscreen launch support.
- [x] Settings update button that pulls the GitHub repo through the local updater service.
- [x] Direct hash routes for tabs, such as `#f1`.
- [x] Halo-style F1 command view with current/next session, weekend stack, standings, results, news, track weather, season rail, and no-spoiler mode.

## Planned Features

### NFL RedZone-Style Football Tab

Goal: rebuild the Football tab into an NFL command center that feels useful on game day and deep enough for normal sports-fan browsing during the week.

- [x] **RedZone Live View**
  - Sunday slate sorted by urgency: live, red zone, close game, scoring drive, favorite teams.
  - Game cards with score, quarter, clock, possession, down/distance, yard line, and last play.
  - Alert rail for touchdowns, turnovers, red-zone trips, final scores, and favorite-team moments.

- [ ] **Game Center**
  - Tap any NFL game to open a focused matchup view.
  - Pregame state: odds, venue, broadcast, team leaders, injury watch, and preview article.
  - Live/post state: drive chart, recent plays, scoring summary, win probability, leaders, box score, and recap/highlights when available.

- [ ] **Players**
  - Search and filter by team, position, and name.
  - Player cards with headshot, team, position, jersey, and current status.
  - Game leaders and season leaders.
  - Later: recent form, fantasy-style stat glance, and player-specific news.

- [ ] **Injuries**
  - League-wide injury board.
  - Filter by team and status: Out, Doubtful, Questionable, IR, or available statuses from the feed.
  - Highlight favorite teams and key offensive players.
  - Link injured players back to team and game views.

- [ ] **Teams**
  - Team profile pages with record, standing, next game, recent results, and favorite toggle.
  - Team stats for offense, defense, passing, rushing, turnovers, and points for/against where available.
  - Roster and player list per team.

- [ ] **News**
  - NFL headline feed.
  - Team-specific news filter.
  - Preview and recap article support from game summaries.

- [ ] **Standings And Playoff Picture**
  - AFC/NFC standings.
  - Division rows.
  - Wild card race.
  - Later: clinched, eliminated, and playoff-seed badges.

- [ ] **Favorite-Team Intelligence**
  - Pin favorite teams higher in the slate.
  - Bubble up favorite-team injuries, news, and live alerts.
  - Keep the app useful even when no favorite team is live.

### NFL Implementation Plan

- [x] Phase 1: build the RedZone Live command view for the Football tab.
- [ ] Phase 2: reuse and expand the existing game detail modal into an NFL Game Center.
- [ ] Phase 3: add Injuries, Players, Teams, News, and Standings segmented panels.
- [x] Phase 4: add favorite-team priority sorting and alert logic.
- [ ] Phase 5: verify the full NFL flow on the Raspberry Pi at 800x480.

First pass added: Football tab command view, urgency-sorted slate, red-zone/one-score/favorite alerts, selected-game panels for Game, Players, Injuries, Teams, and News, and adaptive refresh timing.

### NFL Data Notes

- Primary source should stay ESPN's existing client-side APIs where possible:
  - Scoreboard: `site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard`
  - News: `site.api.espn.com/apis/site/v2/sports/football/nfl/news`
  - Game summary: `site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event=...`
- NashTrack already normalizes useful ESPN summary data for details: injuries, leaders, rosters, plays, win probability, team stats, articles, and videos.
- Avoid new npm dependencies unless a feature truly needs one.
- Keep every NFL view touch-friendly and stable at 800x480.

## Future Sport Command Views

- [ ] NBA courtside command view: live slate, standings, leaders, injuries/news, team/player detail.
- [ ] MLB dugout command view: inning state, probable pitchers, standings, team/player detail.
- [ ] NHL rink command view: live game state, standings, goalie/team stats, injuries/news.
- [ ] Soccer matchday command view: fixtures, live clocks, tables, team/player detail, news.

## Local Run

```powershell
python main.py
```

Use `python main.py --no-open` to start the web server without opening a browser window, or `python main.py --kivy` to run the older Kivy UI.
