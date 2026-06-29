# NashTrack

NashTrack is a compact sports command center built for an 800x480 Raspberry Pi touchscreen. The app runs as a local Vite web UI from `main.py`, opens in a kiosk-style browser window, and keeps a Kivy fallback available with `--kivy`.

## Current Status

- [x] Compact 800x480 dashboard with sidebar, topbar, footer, favorites, calendar, headlines, and upcoming events.
- [x] Web launcher flow through `main.py` and `app/web_launcher.py`.
- [x] Raspberry Pi Chromium fullscreen launch support.
- [x] Settings update controls with Manual mode and opt-in automatic main-branch pulls on the Pi.
- [x] Settings display mode for Raspberry Pi screen sleep after 3 minutes or always-on mode, with backend watchdog and 10-second test.
- [x] Settings launch-at-startup controls for the Raspberry Pi desktop session.
- [x] Dashboard live-score ticker, calendar-forward layout, cycling headline rail, and broadcast/service chips.
- [x] 7-inch touchscreen swipe controls for tickers, headline rail, two-week calendar navigation, and game tabs.
- [x] Direct hash routes for tabs, such as `#f1`.
- [x] Halo-style F1 command view with current/next session, weekend stack, standings, results, news, track weather, season rail, and no-spoiler mode.

## Planned Features

### NFL RedZone-Style Football Tab

Goal: rebuild the Football tab into an NFL command center that feels useful on game day and deep enough for normal sports-fan browsing during the week.

- [x] **RedZone Live View**
  - Sunday slate sorted by urgency: live, red zone, close game, scoring drive, favorite teams.
  - Game cards with score, quarter, clock, possession, down/distance, yard line, and last play.
  - Alert rail for touchdowns, turnovers, red-zone trips, final scores, and favorite-team moments.

- [x] **Game Center**
  - Tap any NFL game to open a focused matchup view.
  - Pregame state: odds, venue, broadcast, team leaders, injury watch, and preview article.
  - Live/post state: drive chart, recent plays, scoring summary, win probability, leaders, box score, and recap/highlights when available.

- [ ] **Players**
  - Search and filter by team, position, and name.
  - Player cards with headshot, team, position, jersey, and current status.
  - Game leaders and season leaders.
  - Later: recent form, fantasy-style stat glance, and player-specific news.

- [x] **Injuries**
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

- [x] **Standings And Playoff Picture**
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
- [x] Phase 2: reuse and expand the existing game detail modal into an NFL Game Center.
- [x] Phase 3: add Injuries, Players, Teams, News, and Standings segmented panels.
- [x] Phase 4: add favorite-team priority sorting and alert logic.
- [ ] Phase 5: verify the full NFL flow on the Raspberry Pi at 800x480.

First pass added: Football tab command view, urgency-sorted slate, red-zone/one-score/favorite alerts, selected-game panels for Game, Players, Injuries, Teams, and News, and adaptive refresh timing.

Second pass added: league-wide ESPN injury board with filters, AFC/NFC playoff standings, division rows, selected-matchup season team stats, and selected-matchup roster support.

Third pass added: redesigned full-game popup as a compact Game Center with matchup header, linescore, game info, odds, live situation, scoring summary, drive chart, team stats, leaders, injuries, football box score groups, article/recap, and highlights when ESPN returns them.

### NFL Data Notes

- Primary source should stay ESPN's existing client-side APIs where possible:
  - Scoreboard: `site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard`
  - News: `site.api.espn.com/apis/site/v2/sports/football/nfl/news`
  - Game summary: `site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event=...`
  - Injuries: `site.api.espn.com/apis/site/v2/sports/football/nfl/injuries`
  - Standings/playoff picture: `site.web.api.espn.com/apis/v2/sports/football/nfl/standings?...`
  - Team stats: `site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}/statistics`
  - Team roster: `site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}/roster`
- NashTrack already normalizes useful ESPN summary data for details: injuries, leaders, rosters, plays, win probability, team stats, articles, and videos.
- Avoid new npm dependencies unless a feature truly needs one.
- Keep every NFL view touch-friendly and stable at 800x480.

## Future Sport Command Views

- [x] NBA courtside command view: live slate, cycling ticker, news rail, and reusable game detail.
- [ ] MLB dugout command view: inning state, probable pitchers, standings, team/player detail.
- [ ] NHL rink command view: live game state, standings, goalie/team stats, injuries/news.
- [x] Soccer matchday command view: fixtures, live clocks, cycling ticker, news rail, and reusable game detail.

## Product Roadmap

### P0 - Foundation And Reliability

- [ ] Split `web/src/main.jsx` into modules:
  - `App.jsx` for shell/routing/state orchestration.
  - `routes/` for Dashboard, Football, F1, Basketball, Soccer, Calendar, and Favorites views.
  - `components/` for Sidebar, Header, ticker, calendar, modals, and settings surfaces.
  - `hooks/` for polling, swipe controls, clock, and screen sleep behavior.
  - `services/` for ESPN, OpenF1, weather, Google Calendar, and local Pi service calls.
  - `utils/` for dates, sports normalization, and broadcast/service mapping.
- [ ] Add a local cache/proxy layer so the Pi serves normalized payloads from endpoints like `/api/dashboard`, `/api/football`, `/api/f1`, `/api/weather`, `/api/calendar`, and `/api/health`.
- [ ] Store last-known-good dashboard data locally so API failures show stale-but-useful cards instead of blank panels.
- [ ] Lock down the local Pi control service by removing wildcard CORS for update/display/startup endpoints and allowing only the NashTrack app origin.
- [ ] Add a launch-time local token or equivalent protection for privileged Pi controls such as update, startup, and display power.
- [ ] Serve the production Vite build from Python for deployed Pi kiosk mode instead of relying on the Vite dev server forever.
- [ ] Add `npm run lint`, `npm run test`, and `npm run build:pi` scripts.

### P1 - First Run And Personalization

- [ ] Build a first-run setup wizard:
  - Screen setup: 800x480 profile, fullscreen, brightness, sleep mode, and touch calibration notes.
  - Favorite setup: sports, leagues, teams, F1 drivers, and F1 constructors.
  - Services: Google Calendar, weather location, launch at startup, and auto-update preference.
  - Demo/live choice so the app looks useful even when no games are live.
- [ ] Replace hardcoded starter favorites with user-managed favorites.
- [ ] Add favorite team picker and favorite sport/league picker.
- [ ] Add "pin this team" actions from game modals and team views.
- [ ] Add "hide this league" controls for dashboard filtering.
- [ ] Use favorite priority sorting across dashboard games, alerts, injuries, news, and upcoming events.
- [ ] Add team-specific headline filtering for Favorites, Football, Basketball, and Soccer.

### P1 - Appliance Dashboard UX

- [ ] Add dashboard density modes:
  - Command Mode: current dense command-center layout.
  - Glance Mode: oversized live score, next event, and favorite-team state.
  - Nightstand Mode: clock, weather, next game, dim visuals, and reduced motion.
- [ ] Rework dashboard flow toward Now / Next / Later:
  - Now: live games, urgent alerts, and live or near-start F1 sessions.
  - Next: games and sessions starting soon.
  - Later: calendar, upcoming slate, and planning context.
- [ ] Expand the RedZone-style alert rail globally for close games, favorite teams live, finals, F1 session starts, upset watch, red-zone trips, and turnovers.
- [ ] Add a one-tap Home/Back zone so touchscreen users never feel stuck inside nested views.
- [ ] Add swipe hints that appear only the first few times, then stay out of the way.
- [ ] Tighten accessibility: `aria-current` for active navigation, better labels for icon-heavy controls, and visible keyboard focus states.
- [ ] Improve empty states with useful next-best context, such as "No NFL games today. Next Cowboys game: Sunday 4:25 PM."
- [ ] Add demo/mock data mode for off-season testing and development.

### P1 - Pi Health And Maintenance

- [ ] Add Pi health panel with Wi-Fi/network status, API health, last successful fetch times, current git commit, update status, CPU temperature, disk free, uptime, display mode, and kiosk/browser status.
- [ ] Surface update mode, last update result, and current app version in Settings and/or the health panel.
- [ ] Add per-service health badges for ESPN, OpenF1, weather, Google Calendar, and the local Pi service.
- [ ] Add local recovery notes/actions for startup launch, display sleep, and failed updates.

### P2 - Sports Depth And Alerts

- [ ] Better TV/service mapping as feeds expose more streaming detail.
- [ ] Calendar conflict warnings for favorite games and F1 sessions that overlap Google Calendar events.
- [ ] No-spoiler mode across all sports, with final scores hidden until tapped or aged out.
- [ ] Favorite-team news filtering and favorite-player/team alert rules.
- [ ] MLB dugout command view with inning state, probable pitchers, standings, team detail, and player detail.
- [ ] NHL rink command view with live game state, standings, goalie/team stats, injuries, and news.
- [ ] Optional sound or visual flash for major events like touchdowns, final scores, red-zone trips, and F1 session starts.

## Local Run

```powershell
python main.py
```

Use `python main.py --no-open` to start the web server without opening a browser window, or `python main.py --kivy` to run the older Kivy UI.

On the Raspberry Pi, launch-at-startup can be enabled in Settings or installed manually:

```bash
bash scripts/pi/install-autostart.sh
```
