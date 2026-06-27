import React, { useState, useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

class F1ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <main style={{ padding: 32, color: "#ff6b6b", fontFamily: "monospace" }}>
          <strong>F1 view crashed:</strong>
          <pre style={{ whiteSpace: "pre-wrap", marginTop: 8 }}>{String(this.state.error)}</pre>
        </main>
      );
    }
    return this.props.children;
  }
}

class ModalErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div className="modal-overlay" onClick={this.props.onClose}>
          <div className="modal-panel" style={{ textAlign: "center", padding: 32 }}>
            <p style={{ color: "#ff6b6b", fontWeight: 700, marginBottom: 8 }}>
              Could not load game details
            </p>
            <p style={{ color: "var(--muted)", fontSize: "var(--fs-meta)", marginBottom: 20 }}>
              {String(this.state.error).slice(0, 120)}
            </p>
            <button className="modal-btn" onClick={this.props.onClose} style={{ maxWidth: 120, margin: "0 auto" }}>
              Close
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─── Icons ────────────────────────────────────────────────────────────────────

const iconPaths = {
  activity: <path d="M3 12h4l3-7 4 14 3-7h4" />,
  barChart: (<><path d="M5 19v-7" /><path d="M12 19V5" /><path d="M19 19v-10" /></>),
  calendar: (<><path d="M7 3v4" /><path d="M17 3v4" /><path d="M4 8h16" /><rect x="4" y="5" width="16" height="16" rx="2" /></>),
  chevronRight: <path d="m9 6 6 6-6 6" />,
  cloudSun: (<><path d="M12 3v2" /><path d="m5.6 5.6 1.4 1.4" /><path d="M3 12h2" /><path d="m18.4 5.6-1.4 1.4" /><path d="M17 12a5 5 0 0 0-9.7-1.7A4.5 4.5 0 1 0 7.5 19H17a3.5 3.5 0 0 0 0-7Z" /></>),
  cloud: (<><path d="M17 12a5 5 0 0 0-9.7-1.7A4.5 4.5 0 1 0 7.5 19H17a3.5 3.5 0 0 0 0-7Z" /></>),
  sun: (<><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" /></>),
  cloudRain: (<><path d="M17 12a5 5 0 0 0-9.7-1.7A4.5 4.5 0 1 0 7.5 19H17a3.5 3.5 0 0 0 0-7Z" /><path d="M10 19v2" /><path d="M14 19v2" /></>),
  cloudSnow: (<><path d="M17 12a5 5 0 0 0-9.7-1.7A4.5 4.5 0 1 0 7.5 19H17a3.5 3.5 0 0 0 0-7Z" /><path d="M10 19v2" /><circle cx="10" cy="22" r="1" /><path d="M14 19v2" /><circle cx="14" cy="22" r="1" /></>),
  zap: <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />,
  gauge: (<><path d="M4 14a8 8 0 1 1 16 0" /><path d="m12 14 4-4" /><path d="M8 18h8" /></>),
  home: (<><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10" /><path d="M10 20v-6h4v6" /></>),
  mapPin: (<><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z" /><circle cx="12" cy="10" r="3" /></>),
  radio: (<><circle cx="12" cy="12" r="2.5" /><path d="M7.7 7.7a6 6 0 0 0 0 8.6" /><path d="M16.3 7.7a6 6 0 0 1 0 8.6" /><path d="M4.9 4.9a10 10 0 0 0 0 14.2" /><path d="M19.1 4.9a10 10 0 0 1 0 14.2" /></>),
  refresh: (<><path d="M20 6v5h-5" /><path d="M4 18v-5h5" /><path d="M18 9a7 7 0 0 0-11.8-3.2L4 8" /><path d="M6 15a7 7 0 0 0 11.8 3.2L20 16" /></>),
  settings: (<><circle cx="12" cy="12" r="3" /><path d="M12 2v3M12 19v3m-7.07-14.07 2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3m-14.07 7.07 2.1-2.1M17 7l2.1-2.1" /></>),
  star: <path d="m12 3 2.8 5.8 6.4.9-4.6 4.5 1.1 6.3-5.7-3-5.7 3 1.1-6.3-4.6-4.5 6.4-.9Z" />,
  trophy: (<><path d="M8 21h8" /><path d="M12 17v4" /><path d="M7 4h10v6a5 5 0 0 1-10 0Z" /><path d="M7 7H4a3 3 0 0 0 3 3" /><path d="M17 7h3a3 3 0 0 1-3 3" /></>),
  tv: (<><rect x="2" y="7" width="20" height="15" rx="2" /><path d="m17 2-5 5-5-5" /></>),
  wifi: (<><path d="M5 12.5a10 10 0 0 1 14 0" /><path d="M8.5 16a5 5 0 0 1 7 0" /><path d="M12 20h.01" /></>),
  x: <path d="M18 6 6 18M6 6l12 12" />,
  link: (<><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" /></>),
  checkCircle: (<><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="m9 11 3 3L22 4" /></>),
  users: (<><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></>),
};

function Icon({ name, size = 20, filled = false }) {
  return (
    <svg aria-hidden="true" className="icon" fill={filled ? "currentColor" : "none"}
      height={size} stroke="currentColor" strokeLinecap="round" strokeLinejoin="round"
      strokeWidth="2" viewBox="0 0 24 24" width={size}>
      {iconPaths[name]}
    </svg>
  );
}

// ─── Hooks ────────────────────────────────────────────────────────────────────

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return now;
}

function useTimeAgo(date) {
  const [label, setLabel] = useState("");
  useEffect(() => {
    function update() {
      if (!date) { setLabel(""); return; }
      const s = Math.floor((Date.now() - date) / 1000);
      if (s < 10) setLabel("Just now");
      else if (s < 60) setLabel(`${s}s ago`);
      else setLabel(`${Math.floor(s / 60)}m ago`);
    }
    update();
    const t = setInterval(update, 5000);
    return () => clearInterval(t);
  }, [date]);
  return label;
}

function useCountdown(target) {
  const [label, setLabel] = useState("");
  useEffect(() => {
    function update() {
      if (!target) { setLabel(""); return; }
      const s = Math.max(0, Math.floor((target - Date.now()) / 1000));
      if (s <= 0) setLabel("now");
      else if (s < 60) setLabel(`${s}s`);
      else setLabel(`${Math.floor(s / 60)}m ${s % 60}s`);
    }
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, [target]);
  return label;
}

// ─── Weather ─────────────────────────────────────────────────────────────────

const WX_CODES = {
  0: ["Clear", "sun"],
  1: ["Mainly Clear", "cloudSun"], 2: ["Partly Cloudy", "cloudSun"], 3: ["Overcast", "cloud"],
  45: ["Foggy", "cloud"], 48: ["Foggy", "cloud"],
  51: ["Drizzle", "cloudRain"], 53: ["Drizzle", "cloudRain"], 55: ["Drizzle", "cloudRain"],
  61: ["Rainy", "cloudRain"], 63: ["Rainy", "cloudRain"], 65: ["Heavy Rain", "cloudRain"],
  71: ["Snowy", "cloudSnow"], 73: ["Snowy", "cloudSnow"], 75: ["Heavy Snow", "cloudSnow"],
  80: ["Showers", "cloudRain"], 81: ["Showers", "cloudRain"], 82: ["Heavy Showers", "cloudRain"],
  95: ["Stormy", "zap"], 96: ["Stormy", "zap"], 99: ["Stormy", "zap"],
};
const DEFAULT_WEATHER_COORDS = { lat: 36.17, lon: -86.78 };
const USE_BROWSER_WEATHER_LOCATION_KEY = "nash-use-browser-location";

function wxInfo(code) {
  for (const [k, v] of Object.entries(WX_CODES)) {
    if (Number(k) === code) return v;
  }
  if (code <= 3) return ["Partly Cloudy", "cloudSun"];
  if (code <= 55) return ["Drizzle", "cloudRain"];
  return ["Cloudy", "cloud"];
}

async function fetchWeather() {
  try {
    let coords = DEFAULT_WEATHER_COORDS;
    if (localStorage.getItem(USE_BROWSER_WEATHER_LOCATION_KEY) === "true" && navigator.geolocation) {
      coords = await new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (p) => resolve({ lat: p.coords.latitude, lon: p.coords.longitude }),
          () => resolve(DEFAULT_WEATHER_COORDS),
          { timeout: 5000 }
        );
      });
    }
    const { lat, lon } = coords;
    const res = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
      `&current=temperature_2m,weather_code&temperature_unit=fahrenheit`
    );
    const data = await res.json();
    const [desc, icon] = wxInfo(data.current.weather_code);
    return { temp: Math.round(data.current.temperature_2m), desc, icon };
  } catch { return null; }
}

// ─── ESPN API ─────────────────────────────────────────────────────────────────

const ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports";

async function fetchScoreboard(sport, league) {
  try {
    const res = await fetch(`${ESPN_BASE}/${sport}/${league}/scoreboard`);
    if (!res.ok) return [];
    return (await res.json()).events || [];
  } catch { return []; }
}

async function fetchNews(sport, league) {
  try {
    const res = await fetch(`${ESPN_BASE}/${sport}/${league}/news?limit=12`);
    if (!res.ok) return [];
    return (await res.json()).articles || [];
  } catch { return []; }
}

async function fetchGameDetail(sport, league, eventId) {
  if (!sport || !league || !eventId) return null;
  try {
    const res = await fetch(`${ESPN_BASE}/${sport}/${league}/summary?event=${eventId}`);
    if (!res.ok) return null;
    const data = await res.json();
    const comp = data.header?.competitions?.[0] || {};
    const venue = comp.venue || data.gameInfo?.venue || {};
    const addr = venue.address || {};

    // Odds — prefer pickcenter (richer), fall back to comp odds
    const pick = Array.isArray(data.pickcenter) ? (data.pickcenter[0] || {}) : {};
    const str = (v) => (v == null || typeof v === "object" ? "" : String(v));
    const spread = str(pick.details) || str(comp.odds?.[0]?.details);
    const overUnder = str(pick.overUnder) || str(comp.odds?.[0]?.overUnder);
    const awayML = pick.awayTeamOdds?.moneyLine;
    const homeML = pick.homeTeamOdds?.moneyLine;
    const formatML = (ml) => ml == null ? "" : ml > 0 ? `+${ml}` : `${ml}`;

    // Per-team season leaders (top 3 stats per team, max 2 leaders per category)
    const teamLeaders = {};
    (Array.isArray(data.leaders) ? data.leaders : []).forEach((cat) => {
      const label = str(cat.shortDisplayName || cat.displayName);
      (Array.isArray(cat.leaders) ? cat.leaders : []).slice(0, 2).forEach((l) => {
        const abbr = str(l.team?.abbreviation);
        if (!abbr) return;
        if (!teamLeaders[abbr]) teamLeaders[abbr] = [];
        if (teamLeaders[abbr].length < 4) {
          teamLeaders[abbr].push({
            category: label,
            name: str(l.athlete?.shortName || l.athlete?.displayName),
            stat: str(l.displayValue),
          });
        }
      });
    });

    // Injury report
    const injuries = (Array.isArray(data.injuries) ? data.injuries : []).flatMap((teamEntry) => {
      const teamAbbr = str(teamEntry.team?.abbreviation);
      return (Array.isArray(teamEntry.injuries) ? teamEntry.injuries : []).map((inj) => ({
        name: str(inj.athlete?.shortName || inj.athlete?.displayName),
        pos: str(inj.athlete?.position?.abbreviation),
        type: str(inj.type),
        status: str(inj.status),
        team: teamAbbr,
      }));
    }).filter((i) => i.name);

    // Live/post: overall top performers across both teams
    const leaders = (Array.isArray(data.leaders) ? data.leaders : []).flatMap((cat) =>
      (Array.isArray(cat.leaders) ? cat.leaders : []).slice(0, 1).map((l) => ({
        category: str(cat.shortDisplayName || cat.displayName),
        name: str(l.athlete?.shortName || l.athlete?.displayName),
        stat: str(l.displayValue),
        team: str(l.team?.abbreviation),
      }))
    ).filter((l) => l.name).slice(0, 6);

    // Rosters: try data.rosters first, fall back to boxscore.players (common for NBA live/pre)
    const rosters = {};
    const mapRosterPlayer = (a) => ({
      name: str(a.athlete?.shortName || a.athlete?.displayName),
      jersey: str(a.athlete?.jersey),
      position: str(a.athlete?.position?.abbreviation),
      headshot: str(a.athlete?.headshot?.href),
    });

    if (Array.isArray(data.rosters) && data.rosters.length) {
      data.rosters.forEach((r) => {
        const abbr = str(r.team?.abbreviation);
        if (!abbr) return;
        const athletes = r.athletes || [];
        rosters[abbr] = {
          starters: athletes.filter((a) => a.starter).map(mapRosterPlayer),
          bench:    athletes.filter((a) => !a.starter && a.active !== false).map(mapRosterPlayer),
        };
      });
    }

    // Fallback: boxscore.players — always populated for live/post, sometimes pre-game too
    (data.boxscore?.players || []).forEach((teamPlayers) => {
      const abbr = str(teamPlayers.team?.abbreviation);
      if (!abbr || rosters[abbr]) return; // skip if already filled from data.rosters
      const stats0 = (teamPlayers.statistics || [])[0] || {};
      const athletes = stats0.athletes || [];
      rosters[abbr] = {
        starters: athletes.filter((a) => a.starter && !a.didNotPlay).map((a) => mapRosterPlayer({ athlete: a.athlete })),
        bench:    athletes.filter((a) => !a.starter && !a.didNotPlay).map((a) => mapRosterPlayer({ athlete: a.athlete })),
      };
    });

    // Team colors (for court avatar accents)
    const teamColors = {};
    (comp.competitors || []).forEach((c) => {
      const abbr = c.team?.abbreviation || "";
      const color = c.team?.color || "";
      if (abbr && color) teamColors[abbr] = `#${color}`;
    });

    // Win probability (last entry = current)
    const wpArr = Array.isArray(data.winprobability) ? data.winprobability : [];
    const lastWP = wpArr.length > 0 ? wpArr[wpArr.length - 1] : null;
    const winProb = lastWP != null ? {
      home: Math.round(lastWP.homeWinPercentage ?? 50),
      away: Math.round(100 - (lastWP.homeWinPercentage ?? 50)),
    } : null;

    // Play-by-play (last 12 plays, most recent first)
    const plays = (Array.isArray(data.plays) ? data.plays : []).slice(-12).reverse().map((p) => ({
      text: str(p.text),
      clock: str(p.clock?.displayValue),
      period: p.period?.number || 0,
      scoring: !!p.scoringPlay,
      awayScore: str(p.awayScore),
      homeScore: str(p.homeScore),
    }));

    // Box score players (keyed MIN/PTS/REB/AST/FG/+/- by column label)
    const boxPlayers = [];
    (data.boxscore?.players || []).forEach((teamPlayers) => {
      const teamAbbr = str(teamPlayers.team?.abbreviation);
      const stats0 = (teamPlayers.statistics || [])[0] || {};
      const labels = (stats0.names || stats0.labels || []).map((l) => String(l).toUpperCase());
      const col = (key) => labels.indexOf(key.toUpperCase());
      const get = (key, row) => { const i = col(key); return i >= 0 ? str(row[i]) : ""; };
      (stats0.athletes || []).forEach((a) => {
        if (a.didNotPlay) return;
        const s = a.stats || [];
        boxPlayers.push({
          name: str(a.athlete?.shortName || a.athlete?.displayName),
          team: teamAbbr,
          starter: !!a.starter,
          min: get("MIN", s),
          pts: get("PTS", s),
          reb: get("REB", s),
          ast: get("AST", s),
          fg:  get("FG", s),
          pm:  get("+/-", s),
        });
      });
    });

    // Team-level box stats for summary row
    const teamStats = {};
    (data.boxscore?.teams || []).forEach((t) => {
      const abbr = str(t.team?.abbreviation);
      if (!abbr) return;
      const sm = {};
      (t.statistics || []).forEach((s) => { sm[str(s.name)] = str(s.displayValue); });
      teamStats[abbr] = {
        pts:      sm.points || sm.totalPoints || "",
        fgPct:    sm.fieldGoalPct || "",
        threePct: sm.threePointFieldGoalPct || "",
        reb:      sm.totalRebounds || "",
        ast:      sm.assists || "",
        to:       sm.turnovers || "",
      };
    });

    // ESPN predictor (pre-game win probability model)
    const pred = data.predictor || null;
    const predictor = (pred?.homeTeam || pred?.awayTeam) ? {
      home: Math.round(parseFloat(pred.homeTeam?.gameProjection) || 0),
      away: Math.round(parseFloat(pred.awayTeam?.gameProjection) || 0),
    } : null;

    // Article (preview / recap)
    const art = data.article || null;
    const article = art ? {
      headline: str(art.headline || art.title),
      story: str(art.story || art.description || "").replace(/<[^>]*>/g, "").slice(0, 700),
    } : null;

    // Video highlights
    const videos = (Array.isArray(data.videos) ? data.videos : []).slice(0, 4).map((v) => ({
      headline: str(v.headline || v.title),
      thumbnail: str(v.thumbnail?.href || v.images?.[0]?.url),
      url: str(v.links?.source?.full?.href || v.links?.web?.href || v.links?.source?.href),
    })).filter((v) => v.thumbnail);

    return {
      venue: str(venue.fullName),
      city: [addr.city, addr.state].filter(Boolean).map(str).join(", "),
      broadcast: str(comp.broadcasts?.[0]?.media?.shortName) || str(comp.broadcasts?.[0]?.names?.[0]),
      spread,
      overUnder,
      awayML: formatML(awayML),
      homeML: formatML(homeML),
      teamLeaders,
      injuries,
      leaders,
      rosters,
      teamColors,
      winProb,
      plays,
      boxPlayers,
      teamStats,
      predictor,
      article,
      videos,
    };
  } catch { return null; }
}

function parseESPNEvent(event, leagueShort, tone, sport, league) {
  const comp = event.competitions?.[0] || {};
  const competitors = comp.competitors || [];
  const away = competitors.find((c) => c.homeAway === "away") || {};
  const home = competitors.find((c) => c.homeAway === "home") || {};
  const status = event.status || {};
  const state = status.type?.state || "pre";
  const gameDate = new Date(comp.date || event.date || "");
  const msElapsed = Date.now() - gameDate.getTime();
  // Treat as live if ESPN says "in", OR if start time passed more than 5min ago (ESPN lag)
  const isLive = state === "in" || (state === "pre" && msElapsed > 5 * 60_000 && msElapsed < 5 * 60 * 60_000);

  const awayScore = away.score ?? "-";
  const homeScore = home.score ?? "-";
  const awayWinning = isLive && Number(away.score) > Number(home.score);
  const homeWinning = isLive && Number(home.score) > Number(away.score);
  // For completed games, highlight winner
  const awayWon = state === "post" && Number(away.score) > Number(home.score);
  const homeWon = state === "post" && Number(home.score) > Number(away.score);

  let progress = 0;
  if (isLive && status.period) {
    const maxPeriods = leagueShort === "NFL" ? 4 : 4;
    progress = Math.min(((status.period - 1) / maxPeriods) * 100 + 12, 94);
  } else if (state === "post") {
    progress = 100;
  }

  const totalRecord = (competitor) =>
    competitor.records?.find((r) => r.type === "total")?.summary || "";

  return {
    id: event.id,
    leagueShort,
    tone,
    sport,
    league,
    away: away.team?.abbreviation || "?",
    home: home.team?.abbreviation || "?",
    awayFull: away.team?.displayName || away.team?.name || "",
    homeFull: home.team?.displayName || home.team?.name || "",
    awayLogo: away.team?.logo || "",
    homeLogo: home.team?.logo || "",
    awayRecord: totalRecord(away),
    homeRecord: totalRecord(home),
    awayScore: String(awayScore),
    homeScore: String(homeScore),
    awayWinning: awayWinning || awayWon,
    homeWinning: homeWinning || homeWon,
    status: status.type?.shortDetail || "Upcoming",
    isLive,
    state,
    progress,
    date: comp.date || event.date || "",
  };
}

async function fetchGoogleCalendarEvents(token) {
  try {
    const now = new Date();
    const timeMin = new Date(now.getFullYear(), now.getMonth(), 1).toISOString();
    const timeMax = new Date(now.getFullYear(), now.getMonth() + 2, 0).toISOString();
    const res = await fetch(
      `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
      `timeMin=${encodeURIComponent(timeMin)}&timeMax=${encodeURIComponent(timeMax)}` +
      `&singleEvents=true&orderBy=startTime&maxResults=50`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (res.status === 401) return null; // expired
    if (!res.ok) return [];
    return (await res.json()).items || [];
  } catch { return []; }
}

// ─── OpenF1 ───────────────────────────────────────────────────────────────────

async function fetchF1(year) {
  try {
    const res = await fetch(`https://api.openf1.org/v1/sessions?year=${year}`);
    if (!res.ok) return [];
    const sessions = await res.json();
    const now = Date.now();
    return sessions
      .filter((s) => new Date(s.date_end).getTime() > now - 3 * 60 * 60 * 1000)
      .sort((a, b) => new Date(a.date_start) - new Date(b.date_start))
      .slice(0, 6)
      .map((s) => {
        const start = new Date(s.date_start).getTime();
        const end = new Date(s.date_end).getTime();
        const isLive = now >= start && now <= end;
        const isPost = now > end;
        return {
          id: `f1-${s.session_key}`,
          leagueShort: "F1",
          tone: "red",
          sport: null,
          league: null,
          away: "F1",
          home: s.session_name,
          awayFull: "Formula 1",
          homeFull: s.session_name,
          awayLogo: "",
          homeLogo: "",
          awayScore: "",
          homeScore: "",
          awayWinning: false,
          homeWinning: false,
          status: isLive ? `Live · ${s.session_name}` : isPost ? s.session_name : s.session_name,
          isLive,
          state: isLive ? "in" : isPost ? "post" : "pre",
          progress: isLive ? 50 : isPost ? 100 : 0,
          date: s.date_start,
          meetingName: s.meeting_name || "Grand Prix",
          location: s.location || "",
        };
      });
  } catch { return []; }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatCountdown(dateStr) {
  if (!dateStr) return "";
  const diff = new Date(dateStr) - Date.now();
  if (diff <= 0) return "Now";
  const h = Math.floor(diff / 3600000);
  const d = Math.floor(h / 24);
  if (d > 0) return `${d}d ${h % 24}h`;
  const m = Math.floor((diff % 3600000) / 60000);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function formatGameTime(dateStr) {
  if (!dateStr) return "";
  try {
    return new Date(dateStr).toLocaleString("en-US", {
      weekday: "short", month: "short", day: "numeric",
      hour: "numeric", minute: "2-digit",
    });
  } catch { return ""; }
}

// ─── Static nav / favorites data ─────────────────────────────────────────────

const navItems = [
  { label: "Dashboard", meta: "All sports", icon: "home" },
  { label: "F1", meta: "2026 Season", icon: "gauge", tone: "red" },
  { label: "Basketball", meta: "NBA scores", icon: "trophy", tone: "orange" },
  { label: "Football", meta: "NFL scores", icon: "activity", tone: "green" },
  { label: "Soccer", meta: "Premier League", icon: "radio" },
];
const utilityNav = [
  { label: "Favorites", meta: "Teams saved", icon: "star" },
  { label: "Calendar", meta: new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" }), icon: "calendar" },
  { label: "Settings", meta: "Preferences", icon: "settings" },
];

function espnGameUrl(game) {
  if (!game?.id || !game?.sport || !game?.league) return "https://www.espn.com/";
  const base = "https://www.espn.com";
  if (game.sport === "soccer") return `${base}/${game.sport}/${game.league}/match/_/gameId/${game.id}`;
  return `${base}/${game.sport}/${game.league}/game/_/gameId/${game.id}`;
}
const favorites = [
  { name: "Ferrari", meta: "F1 team", tag: "FER", logo: "https://a.espncdn.com/i/teamlogos/f1/500/ferrari.png" },
  { name: "LA Lakers", meta: "NBA", tag: "LAL", logo: "https://a.espncdn.com/i/teamlogos/nba/500/lal.png" },
  { name: "Man United", meta: "Soccer", tag: "MU", logo: "https://a.espncdn.com/i/teamlogos/soccer/500/360.png" },
  { name: "Dallas Cowboys", meta: "NFL", tag: "DAL", logo: "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png" },
];

// ─── Shared card components ───────────────────────────────────────────────────

function TeamMark({ label, logo, tone, size = "md" }) {
  const [imgOk, setImgOk] = useState(!!logo);
  useEffect(() => { setImgOk(!!logo); }, [logo]);
  return (
    <div className={`team-mark ${tone || ""} tm-${size}`}>
      {logo && imgOk
        ? <img src={logo} alt={label} className="team-logo" onError={() => setImgOk(false)} />
        : <span className="team-abbrev">{label}</span>}
    </div>
  );
}

function LoadingCard() {
  return <article className="live-card loading-card"><div className="loading-pulse" /></article>;
}

// ─── F1 view data helpers ────────────────────────────────────────────────────

const F1_TEAM_COLORS = {
  "red bull": "#3671c6", "ferrari": "#e8002d", "mercedes": "#27f4d2",
  "mclaren": "#ff8000", "aston martin": "#229971", "alpine": "#0093cc",
  "williams": "#64c4ff", "rb": "#6692ff", "sauber": "#52e252", "haas": "#b6babd",
};

function getTeamColor(name) {
  const n = (name || "").toLowerCase();
  for (const [k, v] of Object.entries(F1_TEAM_COLORS)) {
    if (n.includes(k)) return v;
  }
  return "var(--muted)";
}

const SESSION_ABBREV = {
  "Practice 1": "FP1", "Practice 2": "FP2", "Practice 3": "FP3",
  "Qualifying": "QUAL", "Race": "RACE", "Sprint": "SPR",
  "Sprint Qualifying": "SQ", "Sprint Shootout": "SS",
};

const COUNTRY_FLAGS = {
  "Australia":"🇦🇺","China":"🇨🇳","Japan":"🇯🇵","Bahrain":"🇧🇭","Saudi Arabia":"🇸🇦",
  "United States":"🇺🇸","Italy":"🇮🇹","Monaco":"🇲🇨","Canada":"🇨🇦","Spain":"🇪🇸",
  "Austria":"🇦🇹","United Kingdom":"🇬🇧","Hungary":"🇭🇺","Belgium":"🇧🇪",
  "Netherlands":"🇳🇱","Azerbaijan":"🇦🇿","Singapore":"🇸🇬","Mexico":"🇲🇽",
  "Brazil":"🇧🇷","United Arab Emirates":"🇦🇪","Qatar":"🇶🇦","Abu Dhabi":"🇦🇪",
};

function countryFlag(c) { return COUNTRY_FLAGS[c] || "🏁"; }

async function fetchRawF1Sessions(year) {
  try {
    const res = await fetch(`https://api.openf1.org/v1/sessions?year=${year}`);
    if (!res.ok) return [];
    const data = await res.json();
    if (!Array.isArray(data)) return [];
    if (data.length === 0 && year === new Date().getFullYear()) {
      const res2 = await fetch(`https://api.openf1.org/v1/sessions?year=${year - 1}`);
      if (!res2.ok) return [];
      const data2 = await res2.json();
      return Array.isArray(data2) ? data2 : [];
    }
    return data;
  } catch { return []; }
}

// Always returns what OpenF1 considers "the latest" session (live or most recent)
async function fetchLatestF1Session() {
  try {
    const res = await fetch("https://api.openf1.org/v1/sessions?session_key=latest");
    if (!res.ok) return null;
    const data = await res.json();
    return Array.isArray(data) && data.length > 0 ? data[0] : null;
  } catch { return null; }
}

async function fetchF1Standings() {
  try {
    const res = await fetch("https://api.jolpi.ca/ergast/f1/current/driverStandings.json");
    if (!res.ok) return [];
    const data = await res.json();
    return data.MRData?.StandingsTable?.StandingsLists?.[0]?.DriverStandings || [];
  } catch { return []; }
}

function groupF1ByMeeting(sessions) {
  if (!Array.isArray(sessions)) return [];
  const map = {};
  sessions.forEach((s) => {
    if (!map[s.meeting_key]) {
      map[s.meeting_key] = {
        key: s.meeting_key, name: s.meeting_name,
        country: s.country_name, circuit: s.circuit_short_name,
        sessions: [], raceStart: null, raceEnd: null, firstStart: Infinity,
      };
    }
    const m = map[s.meeting_key];
    m.sessions.push(s);
    const start = new Date(s.date_start).getTime();
    if (start < m.firstStart) m.firstStart = start;
    if (s.session_name === "Race") { m.raceStart = start; m.raceEnd = new Date(s.date_end).getTime(); }
  });
  return Object.values(map)
    .map((m) => ({
      ...m,
      raceStart: m.raceStart || m.firstStart,
      raceEnd: m.raceEnd || Math.max(...m.sessions.map((s) => new Date(s.date_end).getTime())),
      sessions: [...m.sessions].sort((a, b) => new Date(a.date_start) - new Date(b.date_start)),
    }))
    .sort((a, b) => a.firstStart - b.firstStart);
}

// ─── F1 view components ───────────────────────────────────────────────────────

function F1Countdown({ targetDate }) {
  const now = useClock();
  const diff = new Date(targetDate) - now;
  if (diff <= 0) return <span className="f1-cd-live">Underway</span>;
  const d = Math.floor(diff / 86400000);
  const h = Math.floor((diff % 86400000) / 3600000);
  const m = Math.floor((diff % 3600000) / 60000);
  const s = Math.floor((diff % 60000) / 1000);
  const units = d > 0
    ? [[d, "DAYS"], [h, "HRS"], [m, "MIN"]]
    : [[h, "HRS"], [m, "MIN"], [s, "SEC"]];
  return (
    <div className="f1-countdown">
      {units.map(([val, label]) => (
        <div key={label} className="f1-cd-block">
          <span className="f1-cd-num">{String(val).padStart(2, "0")}</span>
          <span className="f1-cd-unit">{label}</span>
        </div>
      ))}
    </div>
  );
}

function F1NextRaceHero({ meeting, nextSession, round, totalRounds, liveSessionOverride }) {
  const now = Date.now();
  // Extend end window by 2h to handle sessions that run over schedule
  const liveSession = liveSessionOverride || meeting.sessions.find(
    (s) => now >= new Date(s.date_start) && now <= new Date(s.date_end).getTime() + 2 * 3600000
  );
  const target = liveSession || nextSession;
  const isLiveWeekend = !!liveSession;

  return (
    <div className="f1-hero panel">
      <div className="f1-hero-eyebrow">
        <span className="f1-badge">F1</span>
        <span>{countryFlag(meeting.country)} {meeting.country}</span>
        {isLiveWeekend
          ? <span className="live-badge">LIVE · {liveSession.session_name}</span>
          : <span className="f1-upcoming-badge">NEXT RACE</span>}
        {round && (
          <span className="f1-round-badge">
            R{String(round).padStart(2, "0")}{totalRounds ? ` / ${totalRounds}` : ""}
          </span>
        )}
      </div>

      <h2 className="f1-hero-title">{meeting.name}</h2>
      <p className="f1-hero-circuit">{meeting.circuit}</p>

      {target && (
        <div className="f1-hero-countdown">
          {liveSession
            ? <span className="f1-cd-live">In Progress</span>
            : <F1Countdown targetDate={target.date_start} />}
          {!liveSession && (
            <span className="f1-cd-label">until {SESSION_ABBREV[target.session_name] || target.session_name}</span>
          )}
        </div>
      )}

      <div className="f1-session-list">
        {meeting.sessions.map((s) => {
          const start = new Date(s.date_start);
          const endExtended = new Date(s.date_end).getTime() + 2 * 3600000;
          const isOverrideMatch = liveSessionOverride && s.session_key === liveSessionOverride.session_key;
          const isLive = isOverrideMatch || (now >= start && now <= endExtended);
          const isDone = !isLive && now > new Date(s.date_end);
          const isNext = s === target && !isLive;
          return (
            <div key={s.session_key} className={`f1-session-row${isDone ? " done" : ""}${isNext ? " next" : ""}${isLive ? " live" : ""}`}>
              <span className="f1-session-dot" />
              <span className="f1-session-abbrev">{SESSION_ABBREV[s.session_name] || s.session_name}</span>
              <span className="f1-session-time">
                {start.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
                {" · "}
                {start.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
              </span>
              {isDone && <span className="f1-tag done">✓</span>}
              {isNext && <span className="f1-tag next">NEXT</span>}
              {isLive && <span className="live-badge" style={{ fontSize: 9 }}>LIVE</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function F1MeetingCard({ meeting, isNext, round }) {
  const now = Date.now();
  const isPast = meeting.raceEnd < now;
  const isLive = meeting.raceStart <= now && meeting.raceEnd >= now;
  const raceDate = meeting.raceStart ? new Date(meeting.raceStart) : null;
  return (
    <article className={`f1-meeting-card${isNext ? " is-next" : ""}${isPast ? " is-past" : ""}${isLive ? " is-live" : ""}`}>
      <span className="f1-mc-flag">{countryFlag(meeting.country)}</span>
      <div className="f1-mc-body">
        <strong>{(meeting.name || "Unknown GP").replace(" Grand Prix", " GP")}</strong>
        <span>{raceDate ? raceDate.toLocaleDateString("en-US", { month: "short", day: "numeric" }) : ""}</span>
      </div>
      {isLive && <span className="live-badge" style={{ fontSize: 9 }}>LIVE</span>}
      {isNext && !isLive && <span className="f1-tag next">NEXT</span>}
      {isPast && <span className="f1-mc-done">✓</span>}
      {round && <span className="f1-mc-round">R{String(round).padStart(2, "0")}</span>}
    </article>
  );
}

function F1DriverRow({ standing }) {
  const teamName = standing.Constructors?.[0]?.name || "";
  const color = getTeamColor(teamName);
  const pts = Number(standing.points);
  const pos = Number(standing.position);
  const posClass = pos === 1 ? " p1" : pos === 2 ? " p2" : pos === 3 ? " p3" : "";
  const topPts = 500;
  return (
    <div className="f1-driver-row">
      <span className={`f1-pos${posClass}`}>{standing.position}</span>
      <div className="f1-team-stripe" style={{ background: color }} />
      <div className="f1-driver-info">
        <strong>{standing.Driver?.code || standing.Driver?.familyName}</strong>
        <span>{teamName}</span>
      </div>
      <div className="f1-pts-col">
        <span className="f1-pts">{standing.points}</span>
        <div className="f1-pts-bar">
          <div className="f1-pts-fill" style={{ width: `${Math.min((pts / topPts) * 100, 100)}%`, background: color }} />
        </div>
      </div>
    </div>
  );
}

function F1View() {
  const [meetings,       setMeetings]       = useState([]);
  const [standings,      setStandings]      = useState([]);
  const [latestSession,  setLatestSession]  = useState(null);
  const [loading,        setLoading]        = useState(true);
  const [error,          setError]          = useState(null);

  useEffect(() => {
    const year = new Date().getFullYear();
    Promise.all([fetchRawF1Sessions(year), fetchF1Standings(), fetchLatestF1Session()])
      .then(([sess, stand, latest]) => {
        try {
          setMeetings(groupF1ByMeeting(sess));
          setStandings(Array.isArray(stand) ? stand : []);
          setLatestSession(latest);
        } catch (e) {
          setError("Failed to process F1 data: " + e.message);
        }
      })
      .catch((e) => setError("Failed to load F1 data: " + e.message))
      .finally(() => setLoading(false));
  }, []);

  const now = Date.now();
  const meetingsWithRound = meetings.map((m, i) => ({ ...m, round: i + 1 }));
  const totalRounds = meetingsWithRound.length;

  // Use the "latest" session from OpenF1 to pin the current race weekend.
  // A meeting is "active" if the latest session belongs to it and started within the last 24h.
  const latestMeeting = latestSession
    ? meetingsWithRound.find((m) => m.key === latestSession.meeting_key)
    : null;
  const latestSessionAge = latestSession
    ? (now - new Date(latestSession.date_start)) / 3600000
    : Infinity;
  const isWeekendActive = latestMeeting && latestSessionAge >= -1 && latestSessionAge <= 24;

  const nextMeeting = isWeekendActive
    ? latestMeeting
    : meetingsWithRound.find((m) => m.raceEnd > now);

  const nextSession = nextMeeting?.sessions.find((s) => new Date(s.date_start) > now);
  const recentMeetings = meetingsWithRound.filter((m) => m.raceEnd < now && m !== nextMeeting).slice(-4);
  const futureMeetings = meetingsWithRound.filter((m) => m !== nextMeeting && m.raceStart > now).slice(0, 6);
  const scheduleMeetings = [...recentMeetings, ...(nextMeeting ? [nextMeeting] : []), ...futureMeetings];

  // Live if: within the session's time window (+2h buffer) OR latestSession is recent (<6h old) and belongs here
  const latestIsRecent = latestSessionAge >= -1 && latestSessionAge <= 6;
  const currentLiveSession = nextMeeting?.sessions.find(
    (s) => now >= new Date(s.date_start) && now <= new Date(s.date_end).getTime() + 2 * 3600000
  ) ?? (latestIsRecent && latestSession?.meeting_key === nextMeeting?.key ? latestSession : null);

  if (loading) return (
    <main className="f1-view">
      <div className="f1-primary">
        <div className="panel" style={{ height: 280, padding: 16 }}>
          <div className="loading-pulse" style={{ height: "100%", borderRadius: 8 }} />
        </div>
        <div className="panel" style={{ height: 120, padding: 16 }}>
          <div className="loading-pulse" style={{ height: "100%", borderRadius: 8 }} />
        </div>
      </div>
      <div className="panel side-card" style={{ height: 400, padding: 16 }}>
        <div className="loading-pulse" style={{ height: "100%", borderRadius: 8 }} />
      </div>
    </main>
  );

  if (error) return (
    <main className="f1-view">
      <div className="panel f1-offseason" style={{ gridColumn: "1/-1", color: "var(--red)" }}>
        <span>⚠️</span><span>{error}</span>
      </div>
    </main>
  );

  return (
    <main className="f1-view">
      <div className="f1-primary">
        {nextMeeting
          ? <F1NextRaceHero meeting={nextMeeting} nextSession={nextSession} round={nextMeeting.round} totalRounds={totalRounds} liveSessionOverride={currentLiveSession} />
          : <div className="panel f1-offseason"><span className="f1-offseason-icon">🏁</span><strong>Season Complete</strong><span>Check back for the next season</span></div>}

        {scheduleMeetings.length > 0 && (
          <section className="panel">
            <div className="section-title">
              <div>
                <h2>Season Schedule</h2>
              </div>
              <span style={{ color: "var(--muted)", fontSize: "var(--fs-meta)" }}>{totalRounds} rounds</span>
            </div>
            <div className="f1-meetings-grid">
              {scheduleMeetings.map((m) => (
                <F1MeetingCard key={m.key} meeting={m} isNext={m === nextMeeting} round={m.round} />
              ))}
            </div>
          </section>
        )}
      </div>

      <aside className="f1-sidebar">
        <section className="panel side-card">
          <div className="side-title">
            <h2>Driver Standings</h2>
            <span style={{ color: "var(--muted)", fontSize: "var(--fs-meta)" }}>{new Date().getFullYear()}</span>
          </div>
          {standings.length > 0
            ? <div className="f1-standings-list">{standings.slice(0, 15).map((s, i) => <F1DriverRow key={i} standing={s} />)}</div>
            : <p className="gcal-empty">No standings available</p>}
        </section>
      </aside>
    </main>
  );
}

// ─── Tab bar ─────────────────────────────────────────────────────────────────

const HALO_F1_TEAM_COLORS = {
  "red bull": "#3671c6", "ferrari": "#e8002d", "mercedes": "#27f4d2",
  "mclaren": "#ff8000", "aston martin": "#229971", "alpine": "#0093cc",
  "williams": "#64c4ff", "rb": "#6692ff", "racing bulls": "#6692ff",
  "sauber": "#52e252", "kick": "#52e252", "haas": "#b6babd",
};

const HALO_F1_SETTINGS_KEY = "nash-f1-settings";
const HALO_F1_REVEALED_KEY = "nash-f1-revealed-results";
const HALO_F1_DEFAULT_SETTINGS = { noSpoilers: true, dimMode: false, activePanel: "standings" };
const HALO_F1_PANELS = [
  { key: "standings", label: "Standings" },
  { key: "results", label: "Results" },
  { key: "news", label: "News" },
  { key: "weather", label: "Weather" },
];
const HALO_F1_SPOILER_NAMES = new Set(["Race", "Sprint", "Qualifying", "Sprint Qualifying", "Sprint Shootout"]);
const HALO_F1_SPOILER_WINDOW = 48 * 60 * 60 * 1000;
const HALO_F1_SESSION_ABBREV = {
  "Practice 1": "FP1", "Practice 2": "FP2", "Practice 3": "FP3",
  "Qualifying": "QUAL", "Race": "RACE", "Sprint": "SPR",
  "Sprint Qualifying": "SQ", "Sprint Shootout": "SS",
};
const HALO_F1_COUNTRY_CODES = {
  Australia: "AUS", China: "CHN", Japan: "JPN", Bahrain: "BHR", "Saudi Arabia": "KSA",
  "United States": "USA", Italy: "ITA", Monaco: "MON", Canada: "CAN", Spain: "ESP",
  Austria: "AUT", "United Kingdom": "GBR", Hungary: "HUN", Belgium: "BEL",
  Netherlands: "NED", Azerbaijan: "AZE", Singapore: "SGP", Mexico: "MEX",
  Brazil: "BRA", "United Arab Emirates": "UAE", Qatar: "QAT", "Abu Dhabi": "UAE",
};

function haloF1TeamColor(name) {
  const clean = String(name || "").toLowerCase();
  for (const [needle, color] of Object.entries(HALO_F1_TEAM_COLORS)) {
    if (clean.includes(needle)) return color;
  }
  return "#98a5b8";
}

function haloF1CountryCode(country) {
  return HALO_F1_COUNTRY_CODES[country] || String(country || "F1").slice(0, 3).toUpperCase();
}

function haloF1SessionLabel(name) {
  return HALO_F1_SESSION_ABBREV[name] || String(name || "F1").slice(0, 4).toUpperCase();
}

function haloF1ApiArray(data) {
  return Array.isArray(data) ? data : [];
}

function haloF1LoadSettings() {
  try {
    return { ...HALO_F1_DEFAULT_SETTINGS, ...JSON.parse(localStorage.getItem(HALO_F1_SETTINGS_KEY) || "{}") };
  } catch {
    return HALO_F1_DEFAULT_SETTINGS;
  }
}

function haloF1LoadRevealed() {
  try {
    return JSON.parse(localStorage.getItem(HALO_F1_REVEALED_KEY) || "{}");
  } catch {
    return {};
  }
}

async function haloF1FetchJson(url, fallback) {
  try {
    const res = await fetch(url);
    if (!res.ok) return fallback;
    return await res.json();
  } catch {
    return fallback;
  }
}

async function haloF1FetchConstructorStandings() {
  const data = await haloF1FetchJson("https://api.jolpi.ca/ergast/f1/current/constructorStandings.json", {});
  return data.MRData?.StandingsTable?.StandingsLists?.[0]?.ConstructorStandings || [];
}

async function haloF1FetchSessionResults(sessionKey) {
  if (!sessionKey) return [];
  return haloF1ApiArray(await haloF1FetchJson(`https://api.openf1.org/v1/session_result?session_key=${sessionKey}`, []));
}

async function haloF1FetchDrivers(sessionKey) {
  if (!sessionKey) return [];
  return haloF1ApiArray(await haloF1FetchJson(`https://api.openf1.org/v1/drivers?session_key=${sessionKey}`, []));
}

async function haloF1FetchWeather(sessionKey) {
  if (!sessionKey) return [];
  return haloF1ApiArray(await haloF1FetchJson(`https://api.openf1.org/v1/weather?session_key=${sessionKey}`, []));
}

async function haloF1FetchNews() {
  return fetchNews("racing", "f1");
}

function haloF1Time(dateStr, style = "short") {
  if (!dateStr) return "TBD";
  try {
    const date = new Date(dateStr);
    if (style === "time") return date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    if (style === "date") return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    return date.toLocaleString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
  } catch {
    return "TBD";
  }
}

function haloF1CountdownText(dateStr, nowMs = Date.now()) {
  if (!dateStr) return "TBD";
  const diff = new Date(dateStr).getTime() - nowMs;
  if (diff <= 0) return "Now";
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  const minutes = Math.floor((diff % 3600000) / 60000);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${Math.max(minutes, 1)}m`;
}

function haloF1NormalizeMeetings(sessions) {
  const grouped = {};
  haloF1ApiArray(sessions).forEach((session) => {
    if (!session?.meeting_key) return;
    if (!grouped[session.meeting_key]) {
      grouped[session.meeting_key] = {
        key: session.meeting_key,
        name: session.meeting_name || "Grand Prix",
        country: session.country_name || "",
        countryCode: haloF1CountryCode(session.country_name),
        circuit: session.circuit_short_name || session.location || "Circuit TBA",
        sessions: [],
        firstStart: Infinity,
        raceStart: 0,
        raceEnd: 0,
      };
    }
    const startMs = new Date(session.date_start).getTime();
    const endMs = new Date(session.date_end).getTime();
    const item = {
      ...session,
      startMs: Number.isFinite(startMs) ? startMs : 0,
      endMs: Number.isFinite(endMs) ? endMs : 0,
      shortName: haloF1SessionLabel(session.session_name),
    };
    const meeting = grouped[session.meeting_key];
    meeting.sessions.push(item);
    if (item.startMs && item.startMs < meeting.firstStart) meeting.firstStart = item.startMs;
    if (session.session_name === "Race") {
      meeting.raceStart = item.startMs;
      meeting.raceEnd = item.endMs;
    }
  });
  return Object.values(grouped)
    .map((meeting) => {
      const ordered = [...meeting.sessions].sort((a, b) => a.startMs - b.startMs);
      const firstStart = meeting.firstStart === Infinity ? ordered[0]?.startMs || 0 : meeting.firstStart;
      const latestEnd = Math.max(...ordered.map((session) => session.endMs || session.startMs || 0));
      return {
        ...meeting,
        firstStart,
        raceStart: meeting.raceStart || firstStart,
        raceEnd: meeting.raceEnd || latestEnd,
        sessions: ordered,
      };
    })
    .sort((a, b) => a.firstStart - b.firstStart)
    .map((meeting, index, list) => ({ ...meeting, round: index + 1, totalRounds: list.length }));
}

function haloF1Context(meetings, latestSession, nowMs) {
  const latestMeeting = latestSession ? meetings.find((meeting) => meeting.key === latestSession.meeting_key) : null;
  const latestAgeHours = latestSession ? (nowMs - new Date(latestSession.date_start).getTime()) / 3600000 : Infinity;
  const activeMeeting = latestMeeting && latestAgeHours >= -1 && latestAgeHours <= 24
    ? latestMeeting
    : meetings.find((meeting) => meeting.raceEnd > nowMs) || meetings[meetings.length - 1] || null;
  const liveSession = activeMeeting?.sessions.find((session) =>
    nowMs >= session.startMs && nowMs <= session.endMs + 2 * 3600000
  ) || (latestAgeHours >= -1 && latestAgeHours <= 6 && latestSession?.meeting_key === activeMeeting?.key ? latestSession : null);
  const nextSession = activeMeeting?.sessions.find((session) => session.startMs > nowMs) || null;
  const completedSessions = activeMeeting?.sessions.filter((session) => session.endMs && session.endMs < nowMs) || [];
  const lastCompleted = completedSessions[completedSessions.length - 1] || null;
  return { meeting: activeMeeting, liveSession, nextSession, lastCompleted, targetSession: liveSession || nextSession || lastCompleted };
}

function haloF1RefreshMs(context, nowMs) {
  if (context.liveSession) return 30000;
  const nextMs = context.nextSession ? context.nextSession.startMs - nowMs : Infinity;
  return nextMs <= 30 * 60 * 1000 ? 60000 : 5 * 60 * 1000;
}

function haloF1SpoilerSession(meetings, nowMs, revealed) {
  return meetings
    .flatMap((meeting) => meeting.sessions.map((session) => ({ ...session, meetingName: meeting.name })))
    .filter((session) =>
      HALO_F1_SPOILER_NAMES.has(session.session_name) &&
      session.endMs < nowMs &&
      nowMs - session.endMs <= HALO_F1_SPOILER_WINDOW &&
      !revealed[String(session.session_key)]
    )
    .sort((a, b) => b.endMs - a.endMs)[0] || null;
}

function haloF1NormalizeDrivers(drivers) {
  const byNumber = {};
  haloF1ApiArray(drivers).forEach((driver) => {
    if (driver.driver_number) byNumber[String(driver.driver_number)] = driver;
  });
  return byNumber;
}

function haloF1NormalizeResults(results, driversByNumber) {
  return haloF1ApiArray(results)
    .map((row, index) => {
      const driver = driversByNumber[String(row.driver_number)] || {};
      const name = driver.broadcast_name || driver.full_name || driver.name_acronym || `#${row.driver_number || index + 1}`;
      return {
        key: `${row.session_key || "result"}-${row.driver_number || index}`,
        position: row.position ?? row.classified_position ?? index + 1,
        code: driver.name_acronym || String(name).split(" ").pop()?.slice(0, 3).toUpperCase() || "DRV",
        driver: String(name).replace(/\s+/g, " ").trim(),
        team: driver.team_name || "",
        color: driver.team_colour ? `#${String(driver.team_colour).replace("#", "")}` : haloF1TeamColor(driver.team_name),
        gap: row.gap_to_leader || row.interval || row.duration || row.status || "",
      };
    })
    .sort((a, b) => Number(a.position) - Number(b.position));
}

function haloF1NormalizeStandings(standings) {
  return haloF1ApiArray(standings).map((standing) => {
    const driver = standing.Driver || {};
    const team = standing.Constructors?.[0]?.name || "";
    return {
      key: driver.driverId || `${standing.position}-${driver.familyName}`,
      position: standing.position,
      code: driver.code || String(driver.familyName || "DRV").slice(0, 3).toUpperCase(),
      team,
      points: standing.points || "0",
      wins: standing.wins || "0",
      color: haloF1TeamColor(team),
    };
  });
}

function haloF1NormalizeConstructors(constructors) {
  return haloF1ApiArray(constructors).slice(0, 5).map((standing) => {
    const name = standing.Constructor?.name || "Constructor";
    return {
      key: standing.Constructor?.constructorId || standing.position,
      name,
      points: standing.points || "0",
      color: haloF1TeamColor(name),
    };
  });
}

function haloF1NormalizeWeather(rows) {
  const latest = haloF1ApiArray(rows).slice(-1)[0];
  if (!latest) return null;
  return {
    label: Number(latest.rainfall) > 0 ? "Wet track" : "Dry track",
    air: latest.air_temperature,
    track: latest.track_temperature,
    humidity: latest.humidity,
    wind: latest.wind_speed,
    pressure: latest.pressure,
  };
}

function haloF1NormalizeNews(articles) {
  return haloF1ApiArray(articles).slice(0, 6).map((article, index) => ({
    key: article.id || article.dataSourceIdentifier || article.headline || index,
    title: article.headline || article.title || "F1 headline",
    meta: article.published
      ? new Date(article.published).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })
      : article.type || "ESPN F1",
    url: article.links?.web?.href || article.link || "",
  }));
}

function HaloF1Countdown({ targetDate }) {
  const now = useClock();
  const diff = new Date(targetDate).getTime() - now.getTime();
  const units = diff <= 0
    ? [["00", "NOW"]]
    : diff >= 86400000
      ? [[Math.floor(diff / 86400000), "DAY"], [Math.floor((diff % 86400000) / 3600000), "HR"]]
      : [[Math.floor(diff / 3600000), "HR"], [Math.floor((diff % 3600000) / 60000), "MIN"], [Math.floor((diff % 60000) / 1000), "SEC"]];
  return (
    <div className="halo-f1-countdown">
      {units.map(([value, label]) => (
        <div className="halo-f1-cd-block" key={label}>
          <span>{String(value).padStart(2, "0")}</span>
          <small>{label}</small>
        </div>
      ))}
    </div>
  );
}

function HaloF1SessionRow({ session, targetSession, liveSession, nowMs }) {
  const isLive = liveSession && session.session_key === liveSession.session_key;
  const isNext = !isLive && targetSession && session.session_key === targetSession.session_key;
  const isDone = !isLive && session.endMs < nowMs;
  return (
    <div className={`halo-f1-session-row${isLive ? " live" : ""}${isNext ? " next" : ""}${isDone ? " done" : ""}`}>
      <span className="halo-f1-session-dot" />
      <strong>{session.shortName}</strong>
      <span>{session.session_name}</span>
      <em>{haloF1Time(session.date_start, "time")}</em>
      {isLive && <b>LIVE</b>}
      {isNext && <b>NEXT</b>}
      {isDone && <b>DONE</b>}
    </div>
  );
}

function HaloF1Hero({ context, totalRounds, nowMs }) {
  const meeting = context.meeting;
  if (!meeting) {
    return (
      <section className="panel halo-f1-hero">
        <div className="halo-f1-empty">
          <strong>F1 season feed waiting</strong>
          <span>OpenF1 has not returned a current schedule yet.</span>
        </div>
      </section>
    );
  }
  const target = context.targetSession;
  const status = context.liveSession ? `LIVE ${context.liveSession.session_name}` : context.nextSession ? "NEXT SESSION" : "RECENT SESSION";
  return (
    <section className="panel halo-f1-hero">
      <div className="halo-f1-hero-top">
        <div className="halo-f1-hero-copy">
          <div className="halo-f1-eyebrow">
            <span className="halo-f1-badge">F1</span>
            <span className="halo-f1-country">{meeting.countryCode}</span>
            <span className={context.liveSession ? "halo-f1-live-chip" : "halo-f1-next-chip"}>{status}</span>
            <span className="halo-f1-round">R{String(meeting.round).padStart(2, "0")} / {totalRounds || meeting.totalRounds}</span>
          </div>
          <h2>{meeting.name}</h2>
          <p>{meeting.circuit} - {meeting.country || "Formula 1"}</p>
          <div className="halo-f1-hero-meta">
            <span>{target?.session_name || "Session"} local</span>
            <strong>{haloF1Time(target?.date_start)}</strong>
          </div>
        </div>
        <div className="halo-f1-clock">
          {context.liveSession
            ? <strong>In progress</strong>
            : target
              ? <HaloF1Countdown targetDate={target.date_start} />
              : <strong>Standby</strong>}
          <small>{target ? haloF1CountdownText(target.date_start, nowMs) : "No target"}</small>
        </div>
      </div>
      <div className="halo-f1-session-stack">
        {meeting.sessions.map((session) => (
          <HaloF1SessionRow
            key={session.session_key}
            session={session}
            targetSession={target}
            liveSession={context.liveSession}
            nowMs={nowMs}
          />
        ))}
      </div>
    </section>
  );
}

function HaloF1SpoilerCover({ subject, session, onReveal }) {
  return (
    <div className="halo-f1-spoiler">
      <div>
        <span>NO SPOILERS</span>
        <strong>{subject} hidden</strong>
        <p>{session?.meetingName || "Recent F1"} {session?.session_name || "session"} finished recently.</p>
      </div>
      <button className="halo-f1-mini-btn reveal" onClick={onReveal}>Reveal</button>
    </div>
  );
}

function HaloF1Standings({ standings, constructors, hidden, spoilerSession, onReveal }) {
  if (hidden) return <HaloF1SpoilerCover subject="Standings" session={spoilerSession} onReveal={onReveal} />;
  return (
    <div className="halo-f1-data-grid">
      <div className="halo-f1-driver-board">
        {standings.slice(0, 10).map((standing) => (
          <div className="halo-f1-driver-row" key={standing.key}>
            <span>{standing.position}</span>
            <i style={{ background: standing.color }} />
            <strong>{standing.code}</strong>
            <em>{standing.team}</em>
            <b>{standing.points}</b>
          </div>
        ))}
        {standings.length === 0 && <p className="gcal-empty">Driver standings unavailable</p>}
      </div>
      <div className="halo-f1-constructor-board">
        <span>CONSTRUCTORS</span>
        {constructors.map((team) => (
          <div className="halo-f1-constructor-row" key={team.key}>
            <i style={{ background: team.color }} />
            <strong>{team.name}</strong>
            <b>{team.points}</b>
          </div>
        ))}
        {constructors.length === 0 && <p className="gcal-empty">Constructor table unavailable</p>}
      </div>
    </div>
  );
}

function HaloF1Results({ results, session, hidden, spoilerSession, onReveal }) {
  if (hidden) return <HaloF1SpoilerCover subject="Results" session={spoilerSession} onReveal={onReveal} />;
  return (
    <div className="halo-f1-results">
      <div className="halo-f1-result-title">
        <span>SESSION RESULT</span>
        <strong>{session?.meeting_name || session?.meetingName || "Latest Session"} - {session?.session_name || "Result"}</strong>
      </div>
      {results.slice(0, 12).map((row) => (
        <div className="halo-f1-result-row" key={row.key}>
          <span>{row.position}</span>
          <i style={{ background: row.color }} />
          <strong>{row.code}</strong>
          <em>{row.gap || row.driver}</em>
        </div>
      ))}
      {results.length === 0 && <p className="gcal-empty">Result feed unavailable for this session</p>}
    </div>
  );
}

function HaloF1News({ articles, hidden, spoilerSession, onReveal }) {
  if (hidden) return <HaloF1SpoilerCover subject="Headlines" session={spoilerSession} onReveal={onReveal} />;
  return (
    <div className="halo-f1-news-list">
      {articles.map((article) => (
        <button
          className="halo-f1-news-row"
          disabled={!article.url}
          key={article.key}
          onClick={() => article.url && window.open(article.url, "_blank")}
        >
          <strong>{article.title}</strong>
          <span>{article.meta}</span>
        </button>
      ))}
      {articles.length === 0 && <p className="gcal-empty">No F1 headlines available</p>}
    </div>
  );
}

function HaloF1Weather({ weather, session }) {
  if (!weather) return <p className="gcal-empty">Track weather feed unavailable</p>;
  const metrics = [
    ["AIR", weather.air == null ? "--" : `${Math.round(weather.air)} C`],
    ["TRACK", weather.track == null ? "--" : `${Math.round(weather.track)} C`],
    ["HUM", weather.humidity == null ? "--" : `${Math.round(weather.humidity)}%`],
    ["WIND", weather.wind == null ? "--" : `${Number(weather.wind).toFixed(1)} m/s`],
  ];
  return (
    <div className="halo-f1-weather">
      <div className="halo-f1-weather-status">
        <span>TRACK WEATHER</span>
        <strong>{weather.label}</strong>
        <p>{session?.meeting_name || "Latest session"} telemetry sample</p>
      </div>
      <div className="halo-f1-weather-grid">
        {metrics.map(([label, value]) => (
          <div className="halo-f1-weather-cell" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function HaloF1DataPanel({ activePanel, setActivePanel, settings, setSettings, data, spoilerSession, revealSpoiler }) {
  const spoilerHidden = !!(settings.noSpoilers && spoilerSession);
  return (
    <section className="panel halo-f1-data-panel">
      <div className="halo-f1-data-header">
        <div className="halo-f1-segments" role="tablist" aria-label="F1 data panels">
          {HALO_F1_PANELS.map((panel) => (
            <button
              className={activePanel === panel.key ? "active" : ""}
              key={panel.key}
              onClick={() => setActivePanel(panel.key)}
            >
              {panel.label}
            </button>
          ))}
        </div>
        <div className="halo-f1-setting-row">
          <button
            className={`halo-f1-mini-btn${settings.noSpoilers ? " active" : ""}`}
            onClick={() => setSettings({ ...settings, noSpoilers: !settings.noSpoilers })}
          >
            No spoilers
          </button>
          <button
            className={`halo-f1-mini-btn${settings.dimMode ? " active" : ""}`}
            onClick={() => setSettings({ ...settings, dimMode: !settings.dimMode })}
          >
            Dim
          </button>
        </div>
      </div>
      <div className="halo-f1-data-body">
        {activePanel === "standings" && (
          <HaloF1Standings
            standings={data.standings}
            constructors={data.constructors}
            hidden={spoilerHidden}
            spoilerSession={spoilerSession}
            onReveal={revealSpoiler}
          />
        )}
        {activePanel === "results" && (
          <HaloF1Results
            results={data.results}
            session={data.resultSession}
            hidden={spoilerHidden}
            spoilerSession={spoilerSession}
            onReveal={revealSpoiler}
          />
        )}
        {activePanel === "news" && (
          <HaloF1News
            articles={data.news}
            hidden={spoilerHidden}
            spoilerSession={spoilerSession}
            onReveal={revealSpoiler}
          />
        )}
        {activePanel === "weather" && <HaloF1Weather weather={data.weather} session={data.weatherSession} />}
      </div>
    </section>
  );
}

function HaloF1SeasonRail({ meetings, activeMeeting, nowMs }) {
  const activeIndex = meetings.findIndex((meeting) => meeting.key === activeMeeting?.key);
  const nextIndex = meetings.findIndex((meeting) => meeting.raceEnd > nowMs);
  const center = activeIndex >= 0 ? activeIndex : Math.max(nextIndex, 0);
  const visible = meetings.slice(Math.max(0, center - 3), Math.min(meetings.length, center + 5));
  return (
    <section className="panel halo-f1-season-panel">
      <div className="halo-f1-panel-title">
        <h2>Season Rail</h2>
        <span>{meetings.length} rounds</span>
      </div>
      <div className="halo-f1-season-rail">
        {visible.map((meeting) => {
          const isActive = meeting.key === activeMeeting?.key;
          const isPast = meeting.raceEnd < nowMs;
          const isLive = meeting.raceStart <= nowMs && meeting.raceEnd + 2 * 3600000 >= nowMs;
          return (
            <article className={`halo-f1-round-card${isActive ? " active" : ""}${isPast ? " past" : ""}${isLive ? " live" : ""}`} key={meeting.key}>
              <span>R{String(meeting.round).padStart(2, "0")}</span>
              <strong>{(meeting.name || "Grand Prix").replace(" Grand Prix", " GP")}</strong>
              <small>{haloF1Time(meeting.raceStart, "date")}</small>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function F1CommandView({ onUpdated, onNextRefresh }) {
  const [meetings, setMeetings] = useState([]);
  const [latestSession, setLatestSession] = useState(null);
  const [standings, setStandings] = useState([]);
  const [constructors, setConstructors] = useState([]);
  const [results, setResults] = useState([]);
  const [weather, setWeather] = useState(null);
  const [news, setNews] = useState([]);
  const [settings, setSettingsState] = useState(haloF1LoadSettings);
  const [revealed, setRevealed] = useState(haloF1LoadRevealed);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const loadRef = useRef(null);

  function saveSettings(next) {
    setSettingsState(next);
    localStorage.setItem(HALO_F1_SETTINGS_KEY, JSON.stringify(next));
  }

  const nowMs = Date.now();
  const context = haloF1Context(meetings, latestSession, nowMs);
  const spoilerSession = haloF1SpoilerSession(meetings, nowMs, revealed);
  const activePanel = HALO_F1_PANELS.some((panel) => panel.key === settings.activePanel)
    ? settings.activePanel
    : "standings";

  function revealSpoiler() {
    if (!spoilerSession) return;
    const next = { ...revealed, [String(spoilerSession.session_key)]: Date.now() };
    setRevealed(next);
    localStorage.setItem(HALO_F1_REVEALED_KEY, JSON.stringify(next));
  }

  loadRef.current = async function loadF1CommandView() {
    const year = new Date().getFullYear();
    const [sessionRows, latest, driverRows, constructorRows, headlines] = await Promise.all([
      fetchRawF1Sessions(year),
      fetchLatestF1Session(),
      fetchF1Standings(),
      haloF1FetchConstructorStandings(),
      haloF1FetchNews(),
    ]);
    const normalizedMeetings = haloF1NormalizeMeetings(sessionRows);
    const loadNowMs = Date.now();
    const loadContext = haloF1Context(normalizedMeetings, latest, loadNowMs);
    const resultSession = loadContext.lastCompleted || loadContext.liveSession || latest;
    const weatherSession = loadContext.liveSession || loadContext.targetSession || latest;
    const [resultRows, driverMeta, weatherRows] = await Promise.all([
      haloF1FetchSessionResults(resultSession?.session_key),
      haloF1FetchDrivers(resultSession?.session_key),
      haloF1FetchWeather(weatherSession?.session_key),
    ]);

    setMeetings(normalizedMeetings);
    setLatestSession(latest);
    setStandings(haloF1NormalizeStandings(driverRows));
    setConstructors(haloF1NormalizeConstructors(constructorRows));
    setResults(haloF1NormalizeResults(resultRows, haloF1NormalizeDrivers(driverMeta)));
    setWeather(haloF1NormalizeWeather(weatherRows));
    setNews(haloF1NormalizeNews(headlines));
    setError(normalizedMeetings.length ? "" : "No F1 schedule returned.");
    setLoading(false);

    const refreshMs = haloF1RefreshMs(loadContext, loadNowMs);
    const updatedAt = new Date();
    if (onUpdated) onUpdated(updatedAt);
    if (onNextRefresh) onNextRefresh(new Date(Date.now() + refreshMs));
    return refreshMs;
  };

  useEffect(() => {
    let timerId;
    let cancelled = false;
    async function run() {
      try {
        const refreshMs = await loadRef.current();
        if (!cancelled) timerId = setTimeout(run, refreshMs);
      } catch (err) {
        if (!cancelled) {
          setError(`Failed to load F1 command view: ${err.message}`);
          setLoading(false);
          timerId = setTimeout(run, 5 * 60 * 1000);
        }
      }
    }
    run();
    return () => {
      cancelled = true;
      clearTimeout(timerId);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return (
      <main className="f1-view halo-f1-view">
        <section className="panel halo-f1-hero halo-f1-loading"><div className="loading-pulse" /></section>
        <section className="panel halo-f1-data-panel halo-f1-loading"><div className="loading-pulse" /></section>
        <section className="panel halo-f1-season-panel halo-f1-loading"><div className="loading-pulse" /></section>
      </main>
    );
  }

  return (
    <main className={`f1-view halo-f1-view${settings.dimMode ? " dimmed" : ""}`}>
      <HaloF1Hero context={context} totalRounds={meetings.length} nowMs={nowMs} />
      {error && <div className="halo-f1-feed-note">{error}</div>}
      <HaloF1DataPanel
        activePanel={activePanel}
        setActivePanel={(panel) => saveSettings({ ...settings, activePanel: panel })}
        settings={settings}
        setSettings={saveSettings}
        data={{
          standings,
          constructors,
          results,
          resultSession: context.lastCompleted || context.liveSession || latestSession,
          weather,
          weatherSession: context.liveSession || context.targetSession || latestSession,
          news,
        }}
        spoilerSession={spoilerSession}
        revealSpoiler={revealSpoiler}
      />
      <HaloF1SeasonRail meetings={meetings} activeMeeting={context.meeting} nowMs={nowMs} />
    </main>
  );
}

function TabBar({ active, onChange, counts }) {
  const tabs = [
    { key: "recent", label: "Recent" },
    { key: "live",   label: "Live" },
    { key: "soon",   label: "Starting Soon" },
  ];
  return (
    <div className="tab-bar">
      {tabs.map(({ key, label }) => (
        <button
          key={key}
          className={`tab-btn ${active === key ? "active" : ""} ${key === "live" && counts.live > 0 ? "has-live" : ""}`}
          onClick={() => onChange(key)}
        >
          {key === "live" && counts.live > 0 && <span className="live-dot-badge" />}
          {label}
          {counts[key] > 0 && <span className="tab-count">{counts[key]}</span>}
        </button>
      ))}
    </div>
  );
}

// ─── Live game command panel ─────────────────────────────────────────────────

function LiveGamePanel({ game }) {
  const [detail, setDetail] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [pulse, setPulse] = useState(false);
  const isF1 = game.leagueShort === "F1";
  const toneColor = {
    orange: "var(--orange)", red: "var(--red)", green: "var(--green)", blue: "#58a6ff",
  }[game.tone] || "var(--blue)";

  useEffect(() => {
    if (isF1 || !game.sport) return;
    let cancelled = false;
    function doFetch() {
      fetchGameDetail(game.sport, game.league, game.id)
        .then((d) => {
          if (cancelled) return;
          setDetail(d);
          setUpdatedAt(new Date());
          setPulse(true);
          setTimeout(() => setPulse(false), 800);
        })
        .catch(() => {});
    }
    doFetch();
    const t = setInterval(doFetch, 30_000);
    return () => { cancelled = true; clearInterval(t); };
  }, [game.id]);

  const plays   = detail?.plays   || [];
  const leaders = detail?.leaders || [];
  const winProb = detail?.winProb || null;
  const teamStats = detail?.teamStats || {};
  const hasStats = Object.keys(teamStats).length > 0;

  const timeStr = updatedAt
    ? updatedAt.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit" })
    : null;

  return (
    <div className={`live-panel${pulse ? " pulse-flash" : ""}`} style={{ "--panel-tone": toneColor, borderLeftColor: toneColor }}>

      {/* ── Header bar ── */}
      <div className="live-panel-header">
        <div className="live-panel-header-left">
          <span className="live-panel-league" style={{ color: toneColor }}>{game.leagueShort}</span>
          <span className="live-badge">LIVE</span>
          <span className="live-panel-status">{game.status}</span>
        </div>
        <span className="live-panel-ts">
          {timeStr ? `Updated ${timeStr}` : "Loading…"}
        </span>
      </div>

      {/* ── Score hero ── */}
      <div className="live-panel-score">
        <div className="live-panel-team away">
          <TeamMark label={game.away} logo={game.awayLogo} tone={game.tone} size="lg" />
          <span className="live-panel-team-name">{game.awayFull || game.away}</span>
        </div>
        <div className="live-panel-nums">
          <span className={`live-panel-num${game.awayWinning ? " winning" : ""}`} style={game.awayWinning ? { color: toneColor } : {}}>
            {game.awayScore}
          </span>
          <span className="live-panel-sep">—</span>
          <span className={`live-panel-num${game.homeWinning ? " winning" : ""}`} style={game.homeWinning ? { color: toneColor } : {}}>
            {game.homeScore}
          </span>
        </div>
        <div className="live-panel-team home">
          <TeamMark label={game.home} logo={game.homeLogo} tone={game.tone} size="lg" />
          <span className="live-panel-team-name">{game.homeFull || game.home}</span>
        </div>
      </div>

      {/* ── Progress bar ── */}
      <div className="live-panel-meter">
        <div className="live-panel-meter-fill" style={{ width: `${game.progress}%`, background: toneColor }} />
      </div>

      {/* ── Win probability ── */}
      {winProb && (
        <div className="live-panel-section">
          <WinProbBar away={winProb.away} home={winProb.home} awayAbbr={game.away} homeAbbr={game.home} toneColor={toneColor} />
        </div>
      )}

      {/* ── Body: plays + stats ── */}
      <div className="live-panel-body">

        {/* Play by play */}
        <div className="live-panel-plays-col">
          <p className="live-panel-col-label">PLAY BY PLAY</p>
          {!detail ? (
            <div className="plays-loading">
              {[...Array(4)].map((_, i) => <div key={i} className="loading-pulse" style={{ height: 34, borderRadius: 5 }} />)}
            </div>
          ) : plays.length === 0 ? (
            <p className="tab-empty" style={{ padding: "12px 0", fontSize: 11 }}>Plays loading…</p>
          ) : (
            <div className="live-panel-plays">
              {plays.slice(0, 6).map((p, i) => (
                <div key={i} className={`live-panel-play${p.scoring ? " scoring" : ""}${i === 0 ? " latest" : ""}`}>
                  <div className="live-panel-play-clock">
                    {p.period > 0 && <span className="play-qtr">Q{p.period}</span>}
                    {p.clock  && <span className="play-time">{p.clock}</span>}
                  </div>
                  <span className="live-panel-play-text">{p.text || "—"}</span>
                  {p.scoring && p.awayScore ? (
                    <span className="live-panel-play-score" style={{ color: toneColor }}>
                      {p.awayScore}–{p.homeScore}
                    </span>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right column: stats + performers */}
        <div className="live-panel-right-col">
          {hasStats && (
            <>
              <p className="live-panel-col-label">TEAM STATS</p>
              <TeamStatsRow awayAbbr={game.away} homeAbbr={game.home} teamStats={teamStats} toneColor={toneColor} />
            </>
          )}

          {leaders.length > 0 && (
            <>
              <p className="live-panel-col-label" style={{ marginTop: hasStats ? 14 : 0 }}>TOP PERFORMERS</p>
              <div className="live-panel-performers">
                {leaders.slice(0, 4).map((l, i) => (
                  <div key={i} className="live-panel-perf">
                    <span className="live-panel-perf-stat" style={{ color: toneColor }}>{l.stat}</span>
                    <span className="live-panel-perf-cat">{l.category}</span>
                    <span className="live-panel-perf-name">{l.name}</span>
                  </div>
                ))}
              </div>
            </>
          )}

          {!detail && (
            <div className="plays-loading" style={{ marginTop: 8 }}>
              {[...Array(3)].map((_, i) => <div key={i} className="loading-pulse" style={{ height: 28, borderRadius: 4 }} />)}
            </div>
          )}
        </div>
      </div>

      {/* ── Lineups ── */}
      {detail && (detail.rosters?.[game.away] || detail.rosters?.[game.home]) && (() => {
        const awayRoster = detail.rosters[game.away] || { starters: [], bench: [] };
        const homeRoster = detail.rosters[game.home] || { starters: [], bench: [] };
        const awayColor = detail.teamColors?.[game.away] || toneColor;
        const homeColor = detail.teamColors?.[game.home] || toneColor;
        const maxStarters = Math.max(awayRoster.starters.length, homeRoster.starters.length);
        if (maxStarters === 0 && awayRoster.bench.length === 0 && homeRoster.bench.length === 0) return null;
        return (
          <div className="live-panel-lineups">
            <div className="live-panel-lineups-header">
              <span style={{ color: awayColor }}>{game.away}</span>
              <p className="live-panel-col-label" style={{ margin: 0 }}>LINEUPS</p>
              <span style={{ color: homeColor, textAlign: "right" }}>{game.home}</span>
            </div>

            {maxStarters > 0 && (
              <div className="live-panel-lineup-rows">
                {Array.from({ length: maxStarters }).map((_, i) => {
                  const a = awayRoster.starters[i];
                  const h = homeRoster.starters[i];
                  return (
                    <div key={i} className="live-panel-lineup-row">
                      <div className="live-panel-lineup-player away">
                        {a && <>
                          <span className="lineup-pos" style={{ color: awayColor }}>{a.position}</span>
                          <span className="lineup-name">{a.name}</span>
                          {a.jersey && <span className="lineup-jersey">#{a.jersey}</span>}
                        </>}
                      </div>
                      <div className="lineup-divider" />
                      <div className="live-panel-lineup-player home">
                        {h && <>
                          {h.jersey && <span className="lineup-jersey">#{h.jersey}</span>}
                          <span className="lineup-name">{h.name}</span>
                          <span className="lineup-pos" style={{ color: homeColor }}>{h.position}</span>
                        </>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {(awayRoster.bench.length > 0 || homeRoster.bench.length > 0) && (
              <div className="live-panel-bench-row">
                <div className="live-panel-bench-side">
                  {awayRoster.bench.slice(0, 6).map((p, i) => (
                    <span key={i} className="lineup-bench-chip" style={{ borderColor: awayColor + "50" }}>
                      {p.name.split(" ").slice(-1)[0]}
                    </span>
                  ))}
                </div>
                <span className="lineup-bench-label">BENCH</span>
                <div className="live-panel-bench-side right">
                  {homeRoster.bench.slice(0, 6).map((p, i) => (
                    <span key={i} className="lineup-bench-chip" style={{ borderColor: homeColor + "50" }}>
                      {p.name.split(" ").slice(-1)[0]}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })()}

    </div>
  );
}

// ─── Game cards ───────────────────────────────────────────────────────────────

function LiveCard({ game, onClick, lastUpdated }) {
  const ago = useTimeAgo(lastUpdated);
  return (
    <article className={`live-card ${game.tone} clickable`} onClick={onClick}>
      <div className="card-league">
        <span>{game.leagueShort}</span>
        <small>{game.status}</small>
      </div>
      {game.leagueShort === "F1" ? (
        <div className="score-row f1-row">
          <strong className="f1-gp">{game.meetingName}</strong>
        </div>
      ) : (
        <div className="score-row">
          <TeamMark label={game.away} logo={game.awayLogo} tone={game.tone} />
          <div className="score-nums">
            <strong className={game.awayWinning ? "winning" : ""}>{game.awayScore}</strong>
            <span>–</span>
            <strong className={game.homeWinning ? "winning" : ""}>{game.homeScore}</strong>
          </div>
          <TeamMark label={game.home} logo={game.homeLogo} tone={game.tone} />
        </div>
      )}
      <div className="team-row">
        <span>{game.away}</span>
        <b>{game.state === "post" ? "FT" : "LIVE"}</b>
        <span>{game.home}</span>
      </div>
      <div className="meter"><span style={{ width: `${game.progress}%` }} /></div>
      {ago && <span className="card-updated">Updated {ago}</span>}
    </article>
  );
}

function SoonCard({ item, onClick }) {
  const isF1 = item.leagueShort === "F1";
  return (
    <article className={`soon-card ${item.tone} clickable`} onClick={onClick}>
      {isF1 ? (
        <span className="soon-league">F1</span>
      ) : (
        <div className="soon-logos">
          <TeamMark label={item.away} logo={item.awayLogo} tone={item.tone} size="sm" />
          <span className="soon-vs">vs</span>
          <TeamMark label={item.home} logo={item.homeLogo} tone={item.tone} size="sm" />
        </div>
      )}
      <strong>{isF1 ? item.meetingName : `${item.away} vs ${item.home}`}</strong>
      <p>{formatGameTime(item.date)}</p>
      <b>{formatCountdown(item.date)}</b>
    </article>
  );
}

// ─── Court / field visualisation ─────────────────────────────────────────────

// NBA halfcourt position slots (SVG viewBox 0 0 100 85, basket near top)
const NBA_POS_SLOTS = {
  PG: { x: 50, y: 66 },
  SG: { x: 74, y: 50 },
  SF: { x: 84, y: 32 },
  PF: { x: 63, y: 22 },
  C:  { x: 50, y: 14 },
};
const NBA_FALLBACK_SLOTS = [
  { x: 50, y: 66 },
  { x: 74, y: 50 },
  { x: 26, y: 50 },
  { x: 63, y: 22 },
  { x: 37, y: 22 },
];

function CourtPlayer({ player, x, y, color, idx }) {
  const [imgOk, setImgOk] = useState(!!player.headshot);
  const initials = player.name.split(" ").map((w) => w[0]).filter(Boolean).join("").slice(0, 2).toUpperCase();
  const clipId = `cp-${idx}-${player.jersey || idx}`;
  return (
    <g transform={`translate(${x},${y})`} style={{ cursor: "default" }}>
      {/* Shadow */}
      <circle r="6.2" fill="rgba(0,0,0,0.4)" transform="translate(0.5,0.8)" />
      {/* Base circle */}
      <circle r="6" fill={color || "#3a7bd5"} />
      {/* Headshot or initials */}
      {imgOk && player.headshot ? (
        <>
          <defs>
            <clipPath id={clipId}>
              <circle r="6" />
            </clipPath>
          </defs>
          <image
            href={player.headshot}
            x="-6" y="-6" width="12" height="12"
            clipPath={`url(#${clipId})`}
            onError={() => setImgOk(false)}
            preserveAspectRatio="xMidYMid slice"
          />
        </>
      ) : (
        <text textAnchor="middle" dominantBaseline="middle" fontSize="4.2" fill="white" fontWeight="800">
          {initials}
        </text>
      )}
      {/* Jersey ring */}
      <circle r="6" fill="none" stroke="rgba(255,255,255,0.35)" strokeWidth="0.6" />
      {/* Name label */}
      <text y="10" textAnchor="middle" fontSize="3.2" fill="rgba(255,255,255,0.85)" fontWeight="600">
        {player.name.split(" ").slice(-1)[0].slice(0, 9)}
      </text>
      {player.jersey && (
        <text y="13.5" textAnchor="middle" fontSize="2.6" fill="rgba(255,255,255,0.5)">
          #{player.jersey}
        </text>
      )}
    </g>
  );
}

function BasketballCourt({ awayAbbr, homeAbbr, rosters, teamColors, toneColor }) {
  const [side, setSide] = useState("home");
  const abbr = side === "home" ? homeAbbr : awayAbbr;
  const roster = rosters?.[abbr] || { starters: [], bench: [] };
  const color = teamColors?.[abbr] || toneColor || "#3a7bd5";

  const getSlot = (player, idx) =>
    NBA_POS_SLOTS[player.position] || NBA_FALLBACK_SLOTS[idx] || NBA_FALLBACK_SLOTS[4];

  return (
    <div className="court-view">
      <div className="court-team-tabs">
        <button
          className={`court-tab${side === "away" ? " active" : ""}`}
          style={side === "away" ? { borderColor: toneColor, color: toneColor } : {}}
          onClick={() => setSide("away")}
        >{awayAbbr}</button>
        <button
          className={`court-tab${side === "home" ? " active" : ""}`}
          style={side === "home" ? { borderColor: toneColor, color: toneColor } : {}}
          onClick={() => setSide("home")}
        >{homeAbbr}</button>
      </div>

      <div className="court-svg-wrap">
        <svg viewBox="0 0 100 85" xmlns="http://www.w3.org/2000/svg" className="court-svg">
          {/* Surface */}
          <rect width="100" height="85" fill="#0c1a27" rx="2"/>
          {/* Court border */}
          <rect x="1" y="1" width="98" height="83" fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="0.7" rx="1"/>
          {/* Half-court line (bottom edge) */}
          <line x1="1" y1="84" x2="99" y2="84" stroke="rgba(255,255,255,0.12)" strokeWidth="0.5"/>
          {/* Key / lane */}
          <rect x="35" y="1" width="30" height="27" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.18)" strokeWidth="0.6"/>
          {/* FT circle upper arc */}
          <path d="M 35,28 A 15 15 0 0 0 65,28" fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="0.6"/>
          {/* FT circle lower arc (dashed) */}
          <path d="M 35,28 A 15 15 0 0 1 65,28" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="0.6" strokeDasharray="1.5,1.5"/>
          {/* Restricted area */}
          <path d="M 44,9 A 6 6 0 0 0 56,9" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="0.5"/>
          {/* Backboard */}
          <line x1="43" y1="3" x2="57" y2="3" stroke="rgba(255,255,255,0.45)" strokeWidth="1.3"/>
          {/* Rim */}
          <circle cx="50" cy="7" r="2.3" fill="none" stroke="rgba(255,140,0,0.75)" strokeWidth="0.9"/>
          {/* 3pt corner lines */}
          <line x1="6" y1="1" x2="6" y2="18" stroke="rgba(255,255,255,0.18)" strokeWidth="0.6"/>
          <line x1="94" y1="1" x2="94" y2="18" stroke="rgba(255,255,255,0.18)" strokeWidth="0.6"/>
          {/* 3pt arc */}
          <path d="M 6,18 A 48 48 0 0 0 94,18" fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth="0.6"/>

          {/* Players */}
          {roster.starters.map((p, i) => {
            const slot = getSlot(p, i);
            return <CourtPlayer key={i} player={p} x={slot.x} y={slot.y} color={color} idx={i} />;
          })}
        </svg>

        {roster.starters.length === 0 && (
          <div className="court-tba">
            <span>Lineup not yet announced</span>
          </div>
        )}
      </div>

      {roster.bench.length > 0 && (
        <div className="court-bench">
          <span className="court-bench-label">BENCH</span>
          <div className="court-bench-row">
            {roster.bench.slice(0, 8).map((p, i) => {
              const initials = p.name.split(" ").map((w) => w[0]).filter(Boolean).join("").slice(0, 2);
              return (
                <div key={i} className="court-bench-player">
                  <div className="court-bench-avatar" style={{ background: color + "30", borderColor: color + "60" }}>
                    <span className="court-bench-initials">{initials}</span>
                    {p.headshot && (
                      <img src={p.headshot} alt="" onError={(e) => { e.target.style.display = "none"; }} />
                    )}
                  </div>
                  <span className="court-bench-name">{p.name.split(" ").slice(-1)[0].slice(0, 8)}</span>
                  <span className="court-bench-pos">{p.position}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Modal sub-components ────────────────────────────────────────────────────

function WinProbBar({ away, home, awayAbbr, homeAbbr, toneColor }) {
  return (
    <div className="winprob">
      <div className="winprob-side">
        <strong className="winprob-pct" style={{ color: toneColor }}>{away}%</strong>
        <span className="winprob-abbr">{awayAbbr}</span>
      </div>
      <div className="winprob-track">
        <div className="winprob-fill" style={{ width: `${away}%`, background: toneColor }} />
      </div>
      <div className="winprob-side right">
        <span className="winprob-abbr">{homeAbbr}</span>
        <strong className="winprob-pct">{home}%</strong>
      </div>
    </div>
  );
}

function TeamStatsRow({ awayAbbr, homeAbbr, teamStats, toneColor }) {
  const a = teamStats[awayAbbr] || {};
  const h = teamStats[homeAbbr] || {};
  const rows = [
    { label: "PTS",  av: a.pts,      hv: h.pts,      higherBetter: true  },
    { label: "FG%",  av: a.fgPct,    hv: h.fgPct,    higherBetter: true  },
    { label: "3P%",  av: a.threePct, hv: h.threePct, higherBetter: true  },
    { label: "REB",  av: a.reb,      hv: h.reb,      higherBetter: true  },
    { label: "AST",  av: a.ast,      hv: h.ast,      higherBetter: true  },
    { label: "TO",   av: a.to,       hv: h.to,       higherBetter: false },
  ].filter((r) => r.av || r.hv);
  if (!rows.length) return null;
  return (
    <div className="modal-pre-section">
      <p className="modal-section-label">TEAM STATS</p>
      <div className="team-stats-grid">
        <span className="team-stats-abbr" style={{ color: toneColor }}>{awayAbbr}</span>
        <span />
        <span className="team-stats-abbr right">{homeAbbr}</span>
        {rows.map((r) => {
          const av = parseFloat(r.av) || 0, hv = parseFloat(r.hv) || 0;
          const awayWins = r.higherBetter ? av > hv : av < hv;
          const homeWins = r.higherBetter ? hv > av : hv < av;
          return [
            <strong key={`a-${r.label}`} className="team-stats-val"
              style={{ color: awayWins ? toneColor : "var(--text)" }}>{r.av}</strong>,
            <span key={`l-${r.label}`} className="team-stats-label">{r.label}</span>,
            <strong key={`h-${r.label}`} className="team-stats-val right"
              style={{ color: homeWins ? toneColor : "var(--text)" }}>{r.hv}</strong>,
          ];
        })}
      </div>
    </div>
  );
}

function PlaysTab({ plays, loading, earlyGame, updatedAt }) {
  if (loading) return (
    <div className="plays-loading">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="loading-pulse" style={{ height: 40, borderRadius: 6 }} />
      ))}
    </div>
  );
  if (!plays.length) return (
    <p className="tab-empty">
      {earlyGame ? "Play-by-play will appear once ESPN starts logging plays" : "No play data yet"}
    </p>
  );
  return (
    <div className="plays-list">
      {updatedAt && (
        <div className="plays-updated">
          <span className="status-dot" style={{ width: 6, height: 6, flexShrink: 0 }} />
          Updated at {updatedAt.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit" })}
        </div>
      )}
      {plays.map((p, i) => (
        <div key={i} className={`play-row${p.scoring ? " scoring" : ""}`}>
          <div className="play-clock">
            {p.period > 0 && <span className="play-qtr">Q{p.period}</span>}
            {p.clock && <span className="play-time">{p.clock}</span>}
          </div>
          <span className="play-text">{p.text || "—"}</span>
          {p.scoring && p.awayScore ? (
            <span className="play-score">{p.awayScore}–{p.homeScore}</span>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function BoxScoreTab({ players, awayAbbr, homeAbbr, toneColor, loading }) {
  const [side, setSide] = useState("away");
  const abbr = side === "away" ? awayAbbr : homeAbbr;
  const team = players.filter((p) => p.team === abbr);
  const starters = team.filter((p) => p.starter);
  const bench = team.filter((p) => !p.starter);

  if (loading) return (
    <div className="plays-loading">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="loading-pulse" style={{ height: 30, borderRadius: 4 }} />
      ))}
    </div>
  );
  if (!team.length) return <p className="tab-empty">Box score not available yet</p>;

  const Row = ({ p }) => (
    <div className="box-row">
      <span className="box-name">{p.name}</span>
      <span className="box-stat">{p.min}</span>
      <span className="box-stat pts" style={{ color: toneColor }}>{p.pts}</span>
      <span className="box-stat">{p.reb}</span>
      <span className="box-stat">{p.ast}</span>
      <span className="box-stat dim">{p.fg}</span>
      <span className="box-stat dim">{p.pm}</span>
    </div>
  );

  return (
    <div className="box-score">
      <div className="court-team-tabs" style={{ marginBottom: 10 }}>
        <button
          className={`court-tab${side === "away" ? " active" : ""}`}
          style={side === "away" ? { color: toneColor, borderColor: toneColor } : {}}
          onClick={() => setSide("away")}
        >{awayAbbr}</button>
        <button
          className={`court-tab${side === "home" ? " active" : ""}`}
          style={side === "home" ? { color: toneColor, borderColor: toneColor } : {}}
          onClick={() => setSide("home")}
        >{homeAbbr}</button>
      </div>
      <div className="box-table">
        <div className="box-row header">
          <span className="box-name">PLAYER</span>
          <span className="box-stat">MIN</span>
          <span className="box-stat">PTS</span>
          <span className="box-stat">REB</span>
          <span className="box-stat">AST</span>
          <span className="box-stat">FG</span>
          <span className="box-stat">+/-</span>
        </div>
        {starters.map((p, i) => <Row key={i} p={p} />)}
        {bench.length > 0 && (
          <>
            <div className="box-divider">BENCH</div>
            {bench.map((p, i) => <Row key={i} p={p} />)}
          </>
        )}
      </div>
    </div>
  );
}

// ─── Game detail modal ────────────────────────────────────────────────────────

function GameDetailModal({ game, onClose }) {
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailUpdatedAt, setDetailUpdatedAt] = useState(null);
  const isF1 = game.leagueShort === "F1";
  const isPost = game.state === "post";
  const isLive = game.isLive;
  const isPre = game.state === "pre";

  const defaultTab = isPre ? "matchup" : isLive ? "score" : "summary";
  const [tab, setTab] = useState(defaultTab);

  // Auto-switch tab when game transitions pre→live or live→post
  useEffect(() => {
    setTab(isPre ? "matchup" : isLive ? "score" : "summary");
  }, [game.state, game.isLive]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (isF1 || !game.sport) return;
    let cancelled = false;
    function doFetch() {
      setDetailLoading(true);
      fetchGameDetail(game.sport, game.league, game.id)
        .then((d) => { if (!cancelled) { setDetail(d); setDetailUpdatedAt(new Date()); } })
        .catch(() => {})
        .finally(() => { if (!cancelled) setDetailLoading(false); });
    }
    doFetch();
    // Auto-refresh detail every 30s while game is live
    let t;
    if (isLive) t = setInterval(doFetch, 30_000);
    return () => { cancelled = true; clearInterval(t); };
  }, [game.id, game.state]); // re-fetch when game goes live or ends

  useEffect(() => {
    function onKey(e) { if (e.key === "Escape") onClose(); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function handleBackdrop(e) { if (e.target === e.currentTarget) onClose(); }

  const toneColor = {
    orange: "var(--orange)", red: "var(--red)", green: "var(--green)", blue: "#58a6ff",
  }[game.tone] || "var(--blue)";

  const awayLeaders = detail?.teamLeaders?.[game.away] || [];
  const homeLeaders = detail?.teamLeaders?.[game.home] || [];
  const hasOdds = detail && (detail.spread || detail.overUnder || detail.awayML || detail.homeML);

  // Tab definitions per game state
  const PRE_TABS  = ["matchup", "preview", "injuries", "lineups"];
  const LIVE_TABS = ["score", "plays", "boxscore"];
  const POST_TABS = ["summary", "boxscore", "recap"];
  const tabs = isPre ? PRE_TABS : isLive ? LIVE_TABS : POST_TABS;
  const TAB_LABELS = {
    matchup: "Matchup", preview: "Preview", injuries: "Injuries", lineups: "Lineups",
    score: "Score", plays: "Play-by-Play", boxscore: "Box Score",
    summary: "Summary", recap: "Recap",
  };

  return (
    <div className="modal-overlay" onClick={handleBackdrop}>
      <div className="modal-panel" style={{ "--modal-tone": toneColor }}>

        {/* ── Header ── */}
        <div className="modal-header">
          <div className="modal-league-row">
            <span className="modal-league" style={{ color: toneColor }}>{game.leagueShort}</span>
            {isLive && <span className="live-badge">LIVE</span>}
            {isPost && <span className="modal-final-badge">FINAL</span>}
          </div>
          <button className="modal-close" onClick={onClose}><Icon name="x" size={18} /></button>
        </div>

        {/* ── Score / Teams hero ── */}
        {isF1 ? (
          <div className="modal-f1-body">
            <div className="modal-f1-icon">🏎</div>
            <strong className="modal-f1-name">{game.meetingName}</strong>
            <span className="modal-f1-session">{game.home}</span>
            {game.location && (
              <span className="modal-f1-loc"><Icon name="mapPin" size={14} /> {game.location}</span>
            )}
            <div className="modal-divider" />
            <div className="modal-time-row">
              <span className="modal-date-str">{formatGameTime(game.date)}</span>
              {isPre && <span className="modal-countdown" style={{ color: toneColor }}>{formatCountdown(game.date)}</span>}
              {isLive && <span className="modal-countdown live-text">In progress</span>}
            </div>
          </div>
        ) : (
          <>
            <div className="modal-teams">
              <div className="modal-team">
                <TeamMark label={game.away} logo={game.awayLogo} tone={game.tone} size="lg" />
                <span className="modal-team-name">{game.awayFull || game.away}</span>
                {game.awayRecord && <span className="modal-team-record">{game.awayRecord}</span>}
              </div>
              <div className="modal-center">
                {(isLive || isPost) ? (
                  <>
                    <div className="modal-score-row">
                      <span className={`modal-score ${game.awayWinning ? "winner" : ""}`}>{game.awayScore}</span>
                      <span className="modal-score-sep">–</span>
                      <span className={`modal-score ${game.homeWinning ? "winner" : ""}`}>{game.homeScore}</span>
                    </div>
                    <span className="modal-status-label">{game.status}</span>
                  </>
                ) : (
                  <>
                    <span className="modal-vs">vs</span>
                    <span className="modal-date-str">{formatGameTime(game.date)}</span>
                    <span className="modal-countdown" style={{ color: toneColor }}>{formatCountdown(game.date)}</span>
                  </>
                )}
              </div>
              <div className="modal-team">
                <TeamMark label={game.home} logo={game.homeLogo} tone={game.tone} size="lg" />
                <span className="modal-team-name">{game.homeFull || game.home}</span>
                {game.homeRecord && <span className="modal-team-record">{game.homeRecord}</span>}
              </div>
            </div>
            {isLive && (
              <div className="modal-progress-bar">
                <div className="modal-progress-fill" style={{ width: `${game.progress}%`, background: toneColor }} />
              </div>
            )}
          </>
        )}

        {/* ── Tab bar (non-F1 only) ── */}
        {!isF1 && (
          <div className="modal-tab-bar">
            {tabs.map((t) => (
              <button
                key={t}
                className={`modal-tab${tab === t ? " active" : ""}`}
                style={tab === t ? { color: toneColor, borderBottomColor: toneColor } : {}}
                onClick={() => setTab(t)}
              >{TAB_LABELS[t]}</button>
            ))}
          </div>
        )}

        {/* ── Tab content ── */}
        {!isF1 && (
          <div className="modal-tab-content">

            {/* ══ PRE-GAME ══ */}

            {tab === "matchup" && (
              <div>
                {detailLoading ? (
                  <div className="modal-meta-skeleton">
                    <div className="loading-pulse" style={{ height: 12, borderRadius: 4 }} />
                    <div className="loading-pulse" style={{ height: 12, width: "55%", borderRadius: 4 }} />
                  </div>
                ) : detail ? (
                  <>
                    <div className="modal-meta">
                      {detail.venue && (
                        <div className="modal-meta-row">
                          <Icon name="mapPin" size={13} />
                          <span>{detail.venue}{detail.city ? ` · ${detail.city}` : ""}</span>
                        </div>
                      )}
                      {detail.broadcast && (
                        <div className="modal-meta-row">
                          <Icon name="tv" size={13} />
                          <span>{detail.broadcast}</span>
                        </div>
                      )}
                    </div>
                    {hasOdds && (
                      <div className="modal-odds-bar">
                        {detail.spread && (
                          <div className="modal-odds-cell">
                            <span className="modal-odds-label">SPREAD</span>
                            <span className="modal-odds-val">{detail.spread}</span>
                          </div>
                        )}
                        {detail.overUnder && (
                          <div className="modal-odds-cell">
                            <span className="modal-odds-label">O/U</span>
                            <span className="modal-odds-val">{detail.overUnder}</span>
                          </div>
                        )}
                        {detail.awayML && (
                          <div className="modal-odds-cell">
                            <span className="modal-odds-label">{game.away} ML</span>
                            <span className="modal-odds-val">{detail.awayML}</span>
                          </div>
                        )}
                        {detail.homeML && (
                          <div className="modal-odds-cell">
                            <span className="modal-odds-label">{game.home} ML</span>
                            <span className="modal-odds-val">{detail.homeML}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                ) : <p className="tab-empty">Loading matchup info…</p>}
              </div>
            )}

            {tab === "preview" && (
              <div>
                {detail?.predictor && (
                  <div className="modal-pre-section">
                    <p className="modal-section-label">ESPN PREDICTOR</p>
                    <WinProbBar
                      away={detail.predictor.away}
                      home={detail.predictor.home}
                      awayAbbr={game.away}
                      homeAbbr={game.home}
                      toneColor={toneColor}
                    />
                  </div>
                )}
                {(awayLeaders.length > 0 || homeLeaders.length > 0) && (
                  <div className="modal-pre-section">
                    <p className="modal-section-label">SEASON LEADERS</p>
                    <div className="modal-two-cols">
                      {[{ abbr: game.away, list: awayLeaders }, { abbr: game.home, list: homeLeaders }].map(({ abbr, list }) => (
                        <div className="modal-leader-col" key={abbr}>
                          <span className="modal-leader-col-header" style={{ color: toneColor }}>{abbr}</span>
                          {list.map((l, i) => (
                            <div className="modal-leader-row" key={i}>
                              <span className="modal-leader-cat">{l.category}</span>
                              <span className="modal-leader-name">{l.name}</span>
                              <strong className="modal-leader-stat" style={{ color: toneColor }}>{l.stat}</strong>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {detailLoading && (
                  <div className="plays-loading">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="loading-pulse" style={{ height: 14, borderRadius: 4 }} />
                    ))}
                  </div>
                )}
                {!detailLoading && !detail?.predictor && awayLeaders.length === 0 && homeLeaders.length === 0 && (
                  <p className="tab-empty">Preview data not available yet</p>
                )}
              </div>
            )}

            {tab === "injuries" && (
              <div>
                {detailLoading ? (
                  <div className="plays-loading">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="loading-pulse" style={{ height: 32, borderRadius: 6 }} />
                    ))}
                  </div>
                ) : detail?.injuries?.length > 0 ? (
                  <div className="modal-injury-list">
                    {detail.injuries.map((inj, i) => {
                      const statusKey = inj.status.toLowerCase().replace(/\s+/g, "-");
                      return (
                        <div className="modal-injury-row" key={i}>
                          <span className={`inj-badge inj-${statusKey}`}>{inj.status.toUpperCase()}</span>
                          <span className="inj-name">{inj.name}</span>
                          <span className="inj-pos">{inj.pos}</span>
                          <span className="inj-team">{inj.team}</span>
                          {inj.type && <span className="inj-type">{inj.type}</span>}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="tab-empty">No injury report available</p>
                )}
              </div>
            )}

            {tab === "lineups" && (
              <BasketballCourt
                awayAbbr={game.away}
                homeAbbr={game.home}
                rosters={detail?.rosters || {}}
                teamColors={detail?.teamColors || {}}
                toneColor={toneColor}
              />
            )}

            {/* ══ LIVE ══ */}

            {tab === "score" && (
              <div>
                {detailLoading && !detail && (
                  <div className="plays-loading">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="loading-pulse" style={{ height: 40, borderRadius: 6 }} />
                    ))}
                  </div>
                )}
                {detail?.venue && (
                  <div className="modal-meta" style={{ marginBottom: 10 }}>
                    <div className="modal-meta-row">
                      <Icon name="mapPin" size={13} />
                      <span>{detail.venue}{detail.city ? ` · ${detail.city}` : ""}</span>
                    </div>
                    {detail.broadcast && (
                      <div className="modal-meta-row">
                        <Icon name="tv" size={13} />
                        <span>{detail.broadcast}</span>
                      </div>
                    )}
                  </div>
                )}
                {detail?.winProb && (
                  <div className="modal-pre-section">
                    <p className="modal-section-label">WIN PROBABILITY</p>
                    <WinProbBar
                      away={detail.winProb.away}
                      home={detail.winProb.home}
                      awayAbbr={game.away}
                      homeAbbr={game.home}
                      toneColor={toneColor}
                    />
                  </div>
                )}
                {detail?.teamStats && Object.keys(detail.teamStats).length > 0 && (
                  <TeamStatsRow
                    awayAbbr={game.away}
                    homeAbbr={game.home}
                    teamStats={detail.teamStats}
                    toneColor={toneColor}
                  />
                )}
                {detail?.leaders?.length > 0 && (
                  <div className="modal-pre-section">
                    <p className="modal-section-label">TOP PERFORMERS</p>
                    <div className="modal-leaders-grid">
                      {detail.leaders.map((l, i) => (
                        <div className="modal-leader-row" key={i}>
                          <span className="modal-leader-cat">{l.category}</span>
                          <span className="modal-leader-name">{l.name}</span>
                          <strong className="modal-leader-stat" style={{ color: toneColor }}>{l.stat}</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {detail && !detail.winProb && !detail.leaders?.length && !Object.keys(detail.teamStats || {}).length && (
                  <p className="tab-empty" style={{ paddingTop: 12 }}>
                    Live stats loading — ESPN takes a minute or two after tip-off
                  </p>
                )}
              </div>
            )}

            {tab === "plays" && (
              <PlaysTab
                plays={detail?.plays || []}
                loading={detailLoading && !detail}
                earlyGame={!!detail && !detail.plays?.length}
                updatedAt={detailUpdatedAt}
              />
            )}

            {tab === "boxscore" && (
              <BoxScoreTab
                players={detail?.boxPlayers || []}
                awayAbbr={game.away}
                homeAbbr={game.home}
                toneColor={toneColor}
                loading={detailLoading && !detail}
              />
            )}

            {/* ══ POST-GAME ══ */}

            {tab === "summary" && (
              <div>
                {detail?.leaders?.length > 0 && (
                  <div className="modal-pre-section">
                    <p className="modal-section-label">TOP PERFORMERS</p>
                    <div className="modal-leaders-grid">
                      {detail.leaders.map((l, i) => (
                        <div className="modal-leader-row" key={i}>
                          <span className="modal-leader-cat">{l.category}</span>
                          <span className="modal-leader-name">{l.name}</span>
                          <strong className="modal-leader-stat" style={{ color: toneColor }}>{l.stat}</strong>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {detail?.teamStats && (
                  <TeamStatsRow
                    awayAbbr={game.away}
                    homeAbbr={game.home}
                    teamStats={detail.teamStats}
                    toneColor={toneColor}
                  />
                )}
                {detailLoading && !detail && (
                  <div className="plays-loading">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="loading-pulse" style={{ height: 40, borderRadius: 6 }} />
                    ))}
                  </div>
                )}
                {!detailLoading && !detail && <p className="tab-empty">Summary not available</p>}
              </div>
            )}

            {tab === "recap" && (
              <div>
                {detailLoading && !detail ? (
                  <div className="plays-loading">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="loading-pulse" style={{ height: 16, borderRadius: 4 }} />
                    ))}
                  </div>
                ) : detail?.article ? (
                  <div className="recap-article">
                    <p className="recap-headline">{detail.article.headline}</p>
                    <p className="recap-story">{detail.article.story}</p>
                  </div>
                ) : (
                  <p className="tab-empty">No recap available</p>
                )}
                {detail?.videos?.length > 0 && (
                  <div className="modal-pre-section">
                    <p className="modal-section-label">HIGHLIGHTS</p>
                    <div className="video-grid">
                      {detail.videos.map((v, i) => (
                        <div className="video-card" key={i}>
                          <img className="video-thumb" src={v.thumbnail} alt={v.headline} />
                          <span className="video-title">{v.headline}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

          </div>
        )}

        {/* ── Close button ── */}
        <div className="modal-actions">
          <button className="modal-btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

// ─── Games section (tabbed) ───────────────────────────────────────────────────

const GAMES_PAGE = 6;

function GamesSection({ liveGames, recentGames, upcomingGames, loading, onSelectGame, activeTab, setActiveTab, lastUpdated }) {
  const [showAll, setShowAll] = useState(false);

  const counts = {
    recent: recentGames.length,
    live: liveGames.length,
    soon: upcomingGames.length,
  };

  const allGames =
    activeTab === "live" ? liveGames :
    activeTab === "recent" ? recentGames :
    upcomingGames;

  const games = showAll ? allGames : allGames.slice(0, GAMES_PAGE);
  const hasMore = allGames.length > GAMES_PAGE;
  const isSoonTab = activeTab === "soon";

  // Reset showAll when tab changes
  React.useEffect(() => { setShowAll(false); }, [activeTab]);

  return (
    <section className="panel">
      <div className="section-title">
        <TabBar active={activeTab} onChange={setActiveTab} counts={counts} />
        {hasMore && !loading && (
          <button className="link-button" onClick={() => setShowAll((v) => !v)}>
            {showAll ? "Show less" : `View all ${allGames.length}`} <Icon name="chevronRight" size={18} />
          </button>
        )}
      </div>

      {loading ? (
        <div className={isSoonTab ? "soon-grid" : "live-grid"}>
          {[0,1,2,3].map((i) => <LoadingCard key={i} />)}
        </div>
      ) : games.length === 0 ? (
        <div className="empty-tab">
          <Icon name="radio" size={28} />
          <span>No {activeTab === "recent" ? "recent" : activeTab === "live" ? "live" : "upcoming"} games right now</span>
        </div>
      ) : isSoonTab ? (
        <div className="soon-grid">
          {games.map((item) => (
            <SoonCard item={item} key={item.id} onClick={() => onSelectGame(item)} />
          ))}
        </div>
      ) : activeTab === "live" ? (
        <div className="live-panels">
          {games.map((game) => (
            <LiveGamePanel game={game} key={game.id} />
          ))}
        </div>
      ) : (
        <div className="live-grid">
          {games.map((game) => (
            <LiveCard game={game} key={game.id} onClick={() => onSelectGame(game)} lastUpdated={lastUpdated} />
          ))}
        </div>
      )}
    </section>
  );
}

// ─── Settings modal ──────────────────────────────────────────────────────────

function SettingsModal({ settings, onSave, onClose, onConnect, onDisconnect }) {
  const [clientId, setClientId] = useState(settings.googleClientId || "");
  const [updateStatus, setUpdateStatus] = useState({ state: "idle", message: "", output: "" });
  const connected = !!settings.googleToken;

  useEffect(() => {
    function onKey(e) { if (e.key === "Escape") onClose(); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function handleBackdrop(e) { if (e.target === e.currentTarget) onClose(); }

  function handleConnect() {
    const id = clientId.trim();
    if (!id) return;
    onSave({ ...settings, googleClientId: id });
    onConnect(id);
  }

  async function handleUpdate() {
    setUpdateStatus({ state: "running", message: "Checking GitHub for updates...", output: "" });
    try {
      const response = await fetch("http://127.0.0.1:5183/update", { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      setUpdateStatus({
        state: payload.ok ? "success" : "error",
        message: payload.message || (response.ok ? "Update complete." : "Update failed."),
        output: payload.output || "",
      });
    } catch (error) {
      setUpdateStatus({
        state: "error",
        message: "Updater is not available. Start Nash Track with main.py, then try again.",
        output: String(error.message || error),
      });
    }
  }

  return (
    <div className="modal-overlay" onClick={handleBackdrop}>
      <div className="modal-panel settings-panel">
        <div className="modal-header">
          <strong style={{ fontSize: 17 }}>Settings</strong>
          <button className="modal-close" onClick={onClose}><Icon name="x" size={18} /></button>
        </div>

        <p className="settings-section-label">Connected Services</p>

        <div className="settings-service-card">
          <div className="settings-service-header">
            <span className="settings-service-icon">📅</span>
            <div className="settings-service-info">
              <strong>Google Calendar</strong>
              <span className={connected ? "connected-text" : "muted-text"}>
                {connected ? "Connected" : "Not connected"}
              </span>
            </div>
            {connected && (
              <button className="settings-disconnect-btn" onClick={onDisconnect}>
                Disconnect
              </button>
            )}
            {connected && <Icon name="checkCircle" size={18} style={{ color: "var(--green)" }} />}
          </div>

          {!connected && (
            <div className="settings-setup">
              <p className="settings-inst-title">How to get your Client ID:</p>
              <ol className="settings-steps">
                <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer">console.cloud.google.com</a></li>
                <li>Create or select a Google Cloud project</li>
                <li>Navigate to <strong>APIs & Services → Library</strong>, search for and enable <strong>Google Calendar API</strong></li>
                <li>Go to <strong>APIs & Services → Credentials</strong></li>
                <li>Click <strong>+ Create Credentials → OAuth 2.0 Client ID</strong></li>
                <li>Set application type to <strong>Web application</strong></li>
                <li>Under <strong>Authorized redirect URIs</strong>, add exactly:<br />
                  <code className="settings-code">{window.location.origin + window.location.pathname}</code>
                </li>
                <li>Click Create — copy the <strong>Client ID</strong> shown</li>
              </ol>

              <div className="settings-input-group">
                <label className="settings-label">Client ID</label>
                <input
                  className="settings-input"
                  type="text"
                  placeholder="xxxxxxxxxxxxxx.apps.googleusercontent.com"
                  value={clientId}
                  onChange={(e) => setClientId(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleConnect()}
                />
              </div>

              <button
                className="settings-connect-btn"
                disabled={!clientId.trim()}
                onClick={handleConnect}
              >
                <Icon name="link" size={16} />
                Authorize with Google
              </button>
            </div>
          )}
        </div>

        <p className="settings-section-label">App Updates</p>

        <div className="settings-service-card">
          <div className="settings-service-header">
            <span className="settings-service-icon">GH</span>
            <div className="settings-service-info">
              <strong>Nash Track GitHub</strong>
              <span className={updateStatus.state === "success" ? "connected-text" : "muted-text"}>
                Pull latest code from the configured origin remote
              </span>
            </div>
            <button
              className="settings-update-btn"
              disabled={updateStatus.state === "running"}
              onClick={handleUpdate}
            >
              <Icon name="refresh" size={15} />
              {updateStatus.state === "running" ? "Updating" : "Pull Update"}
            </button>
          </div>
          {updateStatus.message && (
            <div className={`settings-update-status ${updateStatus.state}`}>
              <strong>{updateStatus.message}</strong>
              {updateStatus.output && <pre>{updateStatus.output}</pre>}
            </div>
          )}
        </div>

        <div className="modal-actions" style={{ marginTop: 16 }}>
          <button className="modal-btn" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────

const NAV_VIEW = {
  "Dashboard": "dashboard", "F1": "f1", "Basketball": "basketball",
  "Football": "football", "Soccer": "soccer",
};
const NAV_ROUTE_KEYS = new Set([...Object.values(NAV_VIEW), "favorites", "calendar"]);

function viewFromHash(hash = window.location.hash) {
  const view = hash.replace(/^#/, "").toLowerCase();
  return NAV_ROUTE_KEYS.has(view) ? view : "dashboard";
}

function Sidebar({ lastUpdated, nextRefresh, onOpenSettings, activeView, onNavigate }) {
  const ago = useTimeAgo(lastUpdated);
  const countdown = useCountdown(nextRefresh);
  return (
    <aside className="sidebar">
      <div className="brand"><span>NASH</span><b>.</b><strong>TRACK</strong></div>
      <nav className="nav-stack">
        {navItems.map(({ label, meta, icon, tone }) => {
          const view = NAV_VIEW[label] || label.toLowerCase();
          return (
            <button
              className={`nav-item ${activeView === view ? "active" : ""} ${tone || ""}`}
              key={label}
              onClick={() => onNavigate(view)}
            >
              <Icon name={icon} size={22} />
              <span className="nav-copy"><strong>{label}</strong><small>{meta}</small></span>
            </button>
          );
        })}
      </nav>
      <div className="nav-divider" />
      <nav className="nav-stack utility">
        {utilityNav.map(({ label, meta, icon }) => (
          <button
            className="nav-item"
            key={label}
            onClick={
              label === "Settings" ? onOpenSettings :
              label === "Calendar" || label === "Favorites" ? () => onNavigate("dashboard") :
              undefined
            }
          >
            <Icon name={icon} size={21} />
            <span className="nav-copy"><strong>{label}</strong><small>{meta}</small></span>
          </button>
        ))}
      </nav>
      <div className="sync-status">
        <span className="status-dot" />
        <div className="sync-lines">
          <span>Updated <strong>{ago || "—"}</strong></span>
          {countdown && <span className="sync-next">Next in <strong>{countdown}</strong></span>}
        </div>
      </div>
    </aside>
  );
}

// ─── Header ──────────────────────────────────────────────────────────────────

function Header({ weather }) {
  const now = useClock();
  const timeStr = now.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  const tzStr = now.toLocaleTimeString("en-US", { timeZoneName: "short" }).split(" ").pop();
  const dateStr = now.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const hour = now.getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <header className="topbar">
      <div>
        <h1>{greeting}, Nash</h1>
        <p>Here's what's happening in your sports world.</p>
      </div>
      <div className="system-strip">
        <div className="time-block">
          <strong>{timeStr}</strong>
          <span>{tzStr}</span>
          <small>{dateStr}</small>
        </div>
        {weather && (
          <div className="weather-pill">
            <Icon name={weather.icon} size={33} />
            <div>
              <strong>{weather.temp}°F</strong>
              <span>{weather.desc}</span>
            </div>
          </div>
        )}
        <Icon name="wifi" size={24} />
      </div>
    </header>
  );
}

// ─── Side panels ─────────────────────────────────────────────────────────────

function CalendarPanel({ googleEvents, connected, sportsGames }) {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();

  // Build Monday-first grid
  const firstDay = new Date(year, month, 1);
  const startDow = (firstDay.getDay() + 6) % 7; // Mon=0 … Sun=6
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells = [];
  for (let i = 0; i < startDow; i++) {
    cells.push({ day: new Date(year, month, 1 - startDow + i).getDate(), muted: true });
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({ day: d, muted: false });
  }
  let fill = 1;
  while (cells.length % 7 !== 0) cells.push({ day: fill++, muted: true });

  // Map sports games → day → first tone color
  const sportsDays = {};
  sportsGames.forEach((g) => {
    if (!g.date) return;
    const d = new Date(g.date);
    if (d.getFullYear() === year && d.getMonth() === month) {
      if (!sportsDays[d.getDate()]) sportsDays[d.getDate()] = g.tone;
    }
  });

  // Google Calendar event days
  const gcalDays = new Set();
  googleEvents.forEach((ev) => {
    const d = new Date(ev.start.dateTime || ev.start.date);
    if (d.getFullYear() === year && d.getMonth() === month) gcalDays.add(d.getDate());
  });

  const todayNum = today.getDate();
  const monthLabel = today.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  const upcomingGcal = googleEvents
    .filter((ev) => new Date(ev.start.dateTime || ev.start.date) >= today)
    .slice(0, 4);

  return (
    <section className="panel side-card calendar-panel">
      <div className="side-title"><h2>Calendar</h2><span className="cal-month">{monthLabel}</span></div>
      <div className="weekday-row">
        {["Mo","Tu","We","Th","Fr","Sa","Su"].map((d) => <span key={d}>{d}</span>)}
      </div>
      <div className="calendar-grid">
        {cells.map(({ day, muted }, i) => {
          const isToday = !muted && day === todayNum;
          const sportTone = !muted && sportsDays[day];
          const hasGcal = !muted && gcalDays.has(day);
          return (
            <button className={`calendar-day${muted ? " muted" : ""}${isToday ? " selected" : ""}`} key={i}>
              {day}
              {(sportTone || hasGcal) && (
                <span className="day-dots">
                  {sportTone && <i className={`day-dot ${sportTone}`} />}
                  {hasGcal && <i className="day-dot gcal" />}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Google Calendar upcoming events list */}
      {connected && upcomingGcal.length > 0 && (
        <div className="gcal-events">
          {upcomingGcal.map((ev, i) => {
            const d = new Date(ev.start.dateTime || ev.start.date);
            const isAllDay = !ev.start.dateTime;
            return (
              <div className="gcal-event-row" key={i}>
                <div className="gcal-event-dot" />
                <div className="gcal-event-copy">
                  <strong>{ev.summary || "(No title)"}</strong>
                  <span>
                    {isAllDay
                      ? d.toLocaleDateString("en-US", { month: "short", day: "numeric" })
                      : d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Legend — always show so user knows what the sport dots mean */}
      <div className="legend">
        <span className="pink">F1</span>
        <span className="orange">NBA</span>
        <span className="blue">Soccer</span>
        <span className="green">NFL</span>
        {connected && <span style={{ color: "#58a6ff" }}>GCal</span>}
      </div>
    </section>
  );
}

function FavoritesPanel() {
  return (
    <section className="panel side-card">
      <div className="side-title"><h2>Favorites</h2></div>
      <div className="favorite-list">
        {favorites.map(({ name, meta, tag, logo }) => (
          <div className="favorite-row" key={name}>
            <div className="mini-logo">
              {logo
                ? <img src={logo} alt={tag} className="mini-logo-img" onError={(e) => { e.target.style.display = "none"; }} />
                : tag}
            </div>
            <div className="row-copy"><strong>{name}</strong><span>{meta}</span></div>
            <Icon name="star" size={16} filled />
          </div>
        ))}
      </div>
    </section>
  );
}

function UpcomingPanel({ events }) {
  return (
    <section className="panel side-card">
      <div className="side-title"><h2>Upcoming Events</h2></div>
      <div className="event-list">
        {events.map(({ name, meta, count, awayLogo }, i) => (
          <div className="event-row" key={i}>
            <div className="event-logos">
              {awayLogo
                ? <img src={awayLogo} alt="" className="event-team-logo" onError={(e) => { e.target.style.display = "none"; }} />
                : <Icon name="radio" size={16} />}
            </div>
            <div className="row-copy"><strong>{name}</strong><span>{meta}</span></div>
            <b>{count}</b>
          </div>
        ))}
      </div>
    </section>
  );
}

function Headlines({ articles }) {
  const [showAll, setShowAll] = useState(false);
  if (!articles.length) return null;
  const visible = showAll ? articles : articles.slice(0, 3);
  return (
    <section className="panel">
      <div className="section-title">
        <div><h2>Top Headlines</h2></div>
        {articles.length > 3 && (
          <button className="link-button" onClick={() => setShowAll((v) => !v)}>
            {showAll ? "Show less" : `+${articles.length - 3} more`} <Icon name="chevronRight" size={18} />
          </button>
        )}
      </div>
      <div className="headline-row">
        {visible.map((a, i) => (
          <article className="headline-card" key={i}
            onClick={() => a.links?.web?.href && window.open(a.links.web.href, "_blank")}
            style={{ cursor: a.links?.web?.href ? "pointer" : "default" }}>
            <div className="headline-thumb"
              style={a.images?.[0]?.url ? { backgroundImage: `url(${a.images[0].url})` } : {}} />
            <div className="row-copy">
              <strong>{a.headline || a.title}</strong>
              <span>
                {a.categories?.[0]?.description || a.type}
                {a.published
                  ? ` · ${new Date(a.published).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}`
                  : ""}
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

// ─── Dashboard ────────────────────────────────────────────────────────────────

const ESPN_FEEDS = [
  { sport: "basketball", league: "nba",   leagueShort: "NBA", tone: "orange" },
  { sport: "football",   league: "nfl",   leagueShort: "NFL", tone: "green"  },
  { sport: "soccer",     league: "eng.1", leagueShort: "EPL", tone: "blue"   },
];

function Dashboard({ onUpdated, googleEvents, googleConnected, onNextRefresh }) {
  const [liveGames,     setLiveGames]     = useState([]);
  const [recentGames,   setRecentGames]   = useState([]);
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [headlines,     setHeadlines]     = useState([]);
  const [upcomingPanel, setUpcomingPanel] = useState([]);
  const [loading,       setLoading]       = useState(true);
  const [activeTab,     setActiveTab]     = useState("soon");
  const [selectedGame,  setSelectedGame]  = useState(null);
  const [lastUpdated,   setLastUpdated]   = useState(null);
  const firstLoadRef = useRef(true);

  const doLoadRef = useRef(null);
  const liveCountRef = useRef(0);
  const soonCountRef = useRef(0);

  doLoadRef.current = async function load() {
    const year = new Date().getFullYear();
    const [espnResults, newsArticles, f1Sessions] = await Promise.all([
      Promise.all(ESPN_FEEDS.map(({ sport, league, leagueShort, tone }) =>
        fetchScoreboard(sport, league).then((evts) =>
          evts.map((e) => parseESPNEvent(e, leagueShort, tone, sport, league))
        )
      )),
      fetchNews("basketball", "nba"),
      fetchF1(year),
    ]);

    const espn = espnResults.flat();
    const allEvents = [...espn, ...f1Sessions];

    const live   = allEvents.filter((g) => g.isLive);
    const recent = allEvents.filter((g) => g.state === "post");
    const soon   = allEvents.filter((g) => !g.isLive && g.state !== "post");

    liveCountRef.current = live.length;
    // Count games within 30min of starting OR overdue (started in last 3h but still "pre")
    const nowMs = Date.now();
    soonCountRef.current = soon.filter((g) => {
      const ms = new Date(g.date).getTime() - nowMs;
      return ms < 30 * 60_000; // within 30 min or already past start time
    }).length;

    setLiveGames(live);
    setRecentGames(recent);
    setUpcomingGames(soon);
    setHeadlines(newsArticles);
    setUpcomingPanel(
      soon.slice(0, 3).map((g) => ({
        name: g.leagueShort === "F1"
          ? `${g.meetingName} — ${g.home}`
          : `${g.away} vs ${g.home}`,
        meta: `${g.leagueShort} · ${formatGameTime(g.date)}`,
        count: formatCountdown(g.date),
        awayLogo: g.awayLogo,
      }))
    );

    // Sync open modal — update snapshot when game state changes
    setSelectedGame((prev) => {
      if (!prev) return prev;
      const fresh = allEvents.find((g) => g.id === prev.id);
      return fresh || prev;
    });

    const now = new Date();
    setLastUpdated(now);
    setLoading(false);
    onUpdated(now);

    // On first load, auto-select the most relevant tab
    if (firstLoadRef.current) {
      firstLoadRef.current = false;
      if (live.length > 0) setActiveTab("live");
      else if (soon.length > 0) setActiveTab("soon");
      else if (recent.length > 0) setActiveTab("recent");
    }
  };

  useEffect(() => {
    doLoadRef.current();
    let timerId;
    function schedule() {
      const ms = liveCountRef.current > 0 ? 30_000
               : soonCountRef.current > 0 ? 60_000
               : 5 * 60_000;
      if (onNextRefresh) onNextRefresh(new Date(Date.now() + ms));
      timerId = setTimeout(async () => {
        await doLoadRef.current();
        schedule();
      }, ms);
    }
    schedule();
    return () => clearTimeout(timerId);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      {selectedGame && (
        <ModalErrorBoundary onClose={() => setSelectedGame(null)}>
          <GameDetailModal game={selectedGame} onClose={() => setSelectedGame(null)} />
        </ModalErrorBoundary>
      )}
      <main className="dashboard">
        <div className="primary-column">
          <GamesSection
            liveGames={liveGames}
            recentGames={recentGames}
            upcomingGames={upcomingGames}
            loading={loading}
            onSelectGame={setSelectedGame}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            lastUpdated={lastUpdated}
          />
          <Headlines articles={headlines} />
        </div>

        <aside className="right-column">
          <CalendarPanel
            googleEvents={googleEvents}
            connected={googleConnected}
            sportsGames={[...liveGames, ...upcomingGames, ...recentGames]}
          />
          <FavoritesPanel />
          <UpcomingPanel events={upcomingPanel} />
        </aside>
      </main>
    </>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

function App() {
  const [weather,      setWeather]      = useState(null);
  const [lastUpdated,  setLastUpdated]  = useState(null);
  const [nextRefresh,  setNextRefresh]  = useState(null);
  const [activeView,   setActiveView]   = useState(() => viewFromHash());
  const [showSettings, setShowSettings] = useState(false);
  const [settings,     setSettings]     = useState(() => {
    try { return JSON.parse(localStorage.getItem("nash-settings") || "{}"); }
    catch { return {}; }
  });
  const [googleToken,  setGoogleToken]  = useState(() => sessionStorage.getItem("gtoken") || null);
  const [calEvents,    setCalEvents]    = useState([]);

  useEffect(() => {
    function syncViewFromHash() {
      if (window.location.hash.includes("access_token")) return;
      setActiveView(viewFromHash());
    }
    window.addEventListener("hashchange", syncViewFromHash);
    syncViewFromHash();
    return () => window.removeEventListener("hashchange", syncViewFromHash);
  }, []);

  // Pick up access_token from Google OAuth redirect (hash fragment)
  useEffect(() => {
    if (!window.location.hash.includes("access_token")) return;
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const token = params.get("access_token");
    if (!token) return;
    sessionStorage.setItem("gtoken", token);
    setGoogleToken(token);
    const next = { ...settings, googleToken: true };
    setSettings(next);
    localStorage.setItem("nash-settings", JSON.stringify(next));
    window.history.replaceState(null, "", window.location.pathname + window.location.search);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Fetch Google Calendar events whenever the token is available
  useEffect(() => {
    if (!googleToken) { setCalEvents([]); return; }
    fetchGoogleCalendarEvents(googleToken).then((events) => {
      if (events === null) {
        // 401 — token expired; clear everything
        sessionStorage.removeItem("gtoken");
        setGoogleToken(null);
        setCalEvents([]);
        const next = { ...settings, googleToken: false };
        setSettings(next);
        localStorage.setItem("nash-settings", JSON.stringify(next));
      } else {
        setCalEvents(events);
      }
    });
  }, [googleToken]); // eslint-disable-line react-hooks/exhaustive-deps

  function saveSettings(next) {
    setSettings(next);
    localStorage.setItem("nash-settings", JSON.stringify(next));
  }

  function connectGoogle(clientId) {
    const redirectUri = window.location.origin + window.location.pathname;
    const url = new URL("https://accounts.google.com/o/oauth2/v2/auth");
    url.searchParams.set("client_id", clientId);
    url.searchParams.set("redirect_uri", redirectUri);
    url.searchParams.set("response_type", "token");
    url.searchParams.set("scope", "https://www.googleapis.com/auth/calendar.readonly");
    window.location.href = url.toString();
  }

  function disconnectGoogle() {
    sessionStorage.removeItem("gtoken");
    setGoogleToken(null);
    setCalEvents([]);
    const next = { ...settings, googleToken: false };
    setSettings(next);
    localStorage.setItem("nash-settings", JSON.stringify(next));
  }

  function navigateView(view) {
    setActiveView(view);
    const url = view === "dashboard"
      ? window.location.pathname + window.location.search
      : `${window.location.pathname}${window.location.search}#${view}`;
    window.history.replaceState(null, "", url);
  }

  useEffect(() => {
    fetchWeather().then(setWeather);
    const t = setInterval(() => fetchWeather().then(setWeather), 30 * 60_000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="app-shell">
      {showSettings && (
        <SettingsModal
          settings={settings}
          onSave={saveSettings}
          onClose={() => setShowSettings(false)}
          onConnect={connectGoogle}
          onDisconnect={disconnectGoogle}
        />
      )}
      <Sidebar
        lastUpdated={lastUpdated}
        nextRefresh={nextRefresh}
        onOpenSettings={() => setShowSettings(true)}
        activeView={activeView}
        onNavigate={navigateView}
      />
      <div className="content-shell">
        <Header weather={weather} />
        {activeView === "f1" ? (
          <F1ErrorBoundary>
            <F1CommandView onUpdated={setLastUpdated} onNextRefresh={setNextRefresh} />
          </F1ErrorBoundary>
        ) : (
          <Dashboard
            onUpdated={setLastUpdated}
            onNextRefresh={setNextRefresh}
            googleEvents={calEvents}
            googleConnected={!!googleToken}
          />
        )}
        <footer className="footer-bar">
          <span>Data provided by</span>
          <strong>ESPN</strong>
          <strong>OPENF1</strong>
          <strong>OPEN-METEO</strong>
          <small>v1.0.0</small>
          <Icon name="refresh" size={16} />
        </footer>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
