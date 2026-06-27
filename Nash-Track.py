"""
Useful links for this project:
https://github.com/pseudo-r/Public-ESPN-API 
 
Quick API examples 
 # NFL Scoreboard
curl "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

# NBA Teams
curl "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"
# MLB Scores for a Specific Date
curl "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard?dates=20241215"
# NHL Standings — NOTE: use /apis/v2/ (not /apis/site/v2/ which returns a stub)
curl "https://site.api.espn.com/apis/v2/sports/hockey/nhl/standings"
    ⚾ Baseball	   baseball	       13   docs/sports/baseball.md
    🏀 Basketball	basketball	    15	docs/sports/basketball.md
    🏈 Football	    football	    5	docs/sports/football.md
    ⚽ Soccer	    soccer	       24	docs/sports/soccer.md

F1 
https://openf1.org/docs/#api-endpoints
https://github.com/FabioRoss/Halo-F1

curl "https://api.openf1.org/v1/car_data?driver_number=55&session_key=9159&speed>=315"


Driver standings	Jolpica / Ergast F1 API
Race calendar & session times	Jolpica / Ergast F1 API
Live session results	OpenF1 API
Timezone offset from IP	IP API
Weather Forecast	Open Meteo
News headlines	The Race — RSS feed

"""

import contextlib
import io
import json

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

import requests

SITE_V2_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
TARGET = {
    "sport": "football",
    "league": "nfl",
    "team_slug": "buf",
    "event_id": "401772988",
}

# Site API v2 (Scores, Teams, Standings)
# https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/{resource}


# Site API v3 (Richer Game Data)
# GET https://site.api.espn.com/apis/site/v3/sports/{sport}/{league}/{resource}

# Core API v2 (Athletes, Stats, Events, Odds)
# GET https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/{resource}

# Core API v3 (Enriched Schema)
# GET https://sports.core.api.espn.com/v3/sports/{sport}/{league}/{resource}

# Search & Web API
# GET https://site.web.api.espn.com/apis/{path}


# CDN API (Real-Time Optimized)
# GET https://cdn.espn.com/core/{sport}/{resource}?xhr=1

# Now API (Real-Time News)
# GET https://now.core.api.espn.com/v1/sports/news


"""
==============================
CORE ROADMAP
==============================

[X] Evaluate APIs per sport
    - ESPN (primary)
    - API-Sports (backup)
    - OpenF1 (F1 telemetry)
    - TheSportsDB (images/logos fallback)

    Goal:
    -> Decide ONE primary source per data type:
        - scores
        - standings
        - players
        - news
        - media/images

## Notes / outcome 
    idk man its ALOT of information.... like most of it seems like duplicated inforamation, or maybe like more than one way to skin a cat type of deal... 
    whatever for now, lets just start with the 

# take away ... 
fuck everything else, just start with the site api v2 

--------------------------------

[ ] Build API Layer (CRITICAL)

    [ ] Generic request wrapper
        - handles:
            - base URL
            - params
            - retries
            - error handling
            - rate limiting

    [ ] Endpoint mapping system
        ex:
            "nfl_scores" -> /scoreboard
            "f1_news"   -> /news

    [ ] Dynamic request builder
        - input:
            sport, team, player, resource
        - output:
            correct endpoint + params

    [ ] (future)
        Natural language → endpoint mapping
        ex:
            "Show me NFL scores"
            -> sport="football"
            -> endpoint="scoreboard"

--------------------------------

[ ] Data Parsing Layer

    [ ] Normalize ALL API responses into ONE format

    Example:
        Raw ESPN JSON -> Clean internal model

    This is HUGE for GUI later.

--------------------------------

[ ] CLI Testing Tool

    Purpose:
        Rapid testing WITHOUT GUI

    Commands:
        python cli.py f1 scoreboard
        python cli.py nfl team DAL
        python cli.py nba news

--------------------------------

[ ] GUI (Kivy)

    Screens:
        - Dashboard (multi-sport)
        - Sport Overview (F1/NFL/etc)
        - Event/Game View
        - Player View
        - Team View

--------------------------------

[ ] Favorites System

    [ ] Save:
        - teams
        - players
    [ ] Store locally (json/db)

--------------------------------

[ ] Player + Team Pages

    [ ] Player stats view
    [ ] Team stats view
    [ ] Game history
    [ ] Upcoming games

--------------------------------

[ ] News + Media

    [ ] Headlines
    [ ] Images
    [ ] Links
"""





import requests

ENDPOINTS = {
    "site_v2_nfl_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
    "site_v2_nba_teams": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams",
    "site_v2_mlb_scoreboard": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
    "site_v2_nfl_news": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/news",
    "site_v2_nfl_summary": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event=401772988",
    "core_v2_nfl_teams": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/teams",
    "core_v2_nfl_athletes": "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/athletes?limit=5",
    "web_search": "https://site.web.api.espn.com/apis/search/v2?query=Josh%20Allen&limit=5",
    "cdn_nfl_scoreboard": "https://cdn.espn.com/core/nfl/scoreboard?xhr=1",
}


def fetch_json(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def build_site_v2_url(sport, league, resource):
    sport = sport.strip().strip("/")
    league = league.strip().strip("/")
    resource = resource.strip().strip("/")

    return f"{SITE_V2_BASE_URL}/{sport}/{league}/{resource}"


def show_top_level(data):
    if isinstance(data, dict):
        print("Top-level keys:")
        for key in list(data.keys())[:15]:
            print(f"  - {key}")
    elif isinstance(data, list):
        print(f"Top-level list with {len(data)} items")
    else:
        print(f"Top-level value: {data}")


def show_scoreboard(data):
    events = data.get("events", [])
    print(f"Games found: {len(events)}")

    for event in events[:5]:
        print()
        print(event.get("name", "Unknown game"))
        print(event.get("status", {}).get("type", {}).get("description", "Unknown status"))

        competitors = event.get("competitions", [{}])[0].get("competitors", [])
        for competitor in competitors:
            team = competitor.get("team", {})
            home_away = competitor.get("homeAway", "?")
            name = team.get("displayName", "Unknown team")
            score = competitor.get("score", "-")
            print(f"  {home_away:5} {name:25} {score}")


def show_site_team(data):
    team = data.get("team", {})
    record_items = team.get("record", {}).get("items", [])
    venue = team.get("franchise", {}).get("venue", {})
    links = team.get("links", [])

    print(team.get("displayName", "Unknown team"))
    print(f"ID: {team.get('id', '?')}")
    print(f"Abbreviation: {team.get('abbreviation', '?')}")
    print(f"Standing: {team.get('standingSummary', 'Unknown')}")

    if record_items:
        print("Records:")
        for record in record_items[:3]:
            label = record.get("description", record.get("type", "record"))
            summary = record.get("summary", "?")
            print(f"  - {label}: {summary}")

    if venue:
        print(f"Venue: {venue.get('fullName', 'Unknown venue')}")

    print("Useful links:")
    for link in links[:5]:
        print(f"  - {link.get('text', 'Link')}: {link.get('href', '')}")


def show_teams(data):
    teams = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
    print(f"Teams found: {len(teams)}")

    for team_wrapper in teams[:10]:
        team = team_wrapper.get("team", {})
        abbreviation = team.get("abbreviation", "")
        display_name = team.get("displayName", "Unknown team")
        print(f"  {abbreviation:5} {display_name}")


def show_news(data):
    articles = data.get("articles", [])
    print(f"Articles found: {len(articles)}")

    for article in articles[:5]:
        headline = article.get("headline", "No headline")
        description = article.get("description", "")
        print()
        print(headline)
        if description:
            print(f"  {description[:120]}...")


def show_core_collection(data):
    count = data.get("count", "?")
    page_index = data.get("pageIndex", "?")
    page_count = data.get("pageCount", "?")
    items = data.get("items", [])

    print(f"Count: {count}")
    print(f"Page: {page_index} of {page_count}")
    print("First item links:")

    for item in items[:5]:
        print(f"  - {item.get('$ref', item)}")


def show_search(data):
    results = data.get("results", [])
    print(f"Result groups found: {len(results)}")

    for result in results[:5]:
        result_type = result.get("type", "unknown")
        total_found = result.get("totalFound", "?")
        contents = result.get("contents", [])
        print()
        print(f"{result_type} results: {total_found}")

        for content in contents[:3]:
            display_name = content.get("displayName", "Unknown result")
            subtitle = content.get("subtitle", "")
            print(f"  - {display_name} {subtitle}")


def show_summary(data):
    header = data.get("header", {})
    competitions = header.get("competitions", [])

    print(header.get("name", "Unknown summary"))
    if competitions:
        status = competitions[0].get("status", {}).get("type", {}).get("description", "")
        print(f"Status: {status}")

    boxscore = data.get("boxscore", {})
    teams = boxscore.get("teams", [])
    print(f"Boxscore teams: {len(teams)}")

    leaders = data.get("leaders", [])
    print(f"Leader sections: {len(leaders)}")


def show_cdn_scoreboard(data):
    content = data.get("content", {})
    scoreboard_data = content.get("sbData", {})
    events = scoreboard_data.get("events", [])
    date_params = content.get("dateParams", {})

    print(f"League: {content.get('league', 'unknown')}")
    print(f"Date params: {date_params}")
    print(f"Games found: {len(events)}")

    for event in events[:5]:
        print(f"  - {event.get('name', 'Unknown game')} ({event.get('date', 'no date')})")


def show_endpoint(name, url):
    print("=" * 70)
    print(name)
    print(url)
    print("-" * 70)

    try:
        data = fetch_json(url)
    except requests.RequestException as error:
        print(f"Request failed: {error}")
        return

    show_top_level(data)
    print()

    if "scoreboard" in name and "cdn" not in name:
        show_scoreboard(data)
    elif "teams" in name and "site_v2" in name:
        show_teams(data)
    elif "news" in name:
        show_news(data)
    elif "core_v2" in name:
        show_core_collection(data)
    elif "search" in name:
        show_search(data)
    elif "summary" in name:
        show_summary(data)
    elif "cdn" in name and "scoreboard" in name:
        show_cdn_scoreboard(data)
    else:
        print("No custom preview yet. The top-level keys above are the first clue.")

    print()


def render_site_v2_preview(resource, data):
    output = io.StringIO()

    with contextlib.redirect_stdout(output):
        show_top_level(data)
        print()

        if resource.startswith("scoreboard"):
            show_scoreboard(data)
        elif resource.startswith("teams/"):
            show_site_team(data)
        elif resource == "teams":
            show_teams(data)
        elif resource.startswith("news"):
            show_news(data)
        elif resource.startswith("summary"):
            show_summary(data)
        else:
            print("No custom preview yet.")
            print("Raw JSON sample:")
            print(json.dumps(data, indent=2)[:3000])

    return output.getvalue()


class NashTrackApp(App):
    def build(self):
        self.title = "Nash Track - ESPN Site API v2"

        main = BoxLayout(orientation="vertical", padding=12, spacing=10)

        controls = BoxLayout(orientation="horizontal", size_hint_y=None, height=72, spacing=8)
        self.sport_input = self.make_labeled_input(controls, "Sport", TARGET["sport"])
        self.league_input = self.make_labeled_input(controls, "League", TARGET["league"])
        self.resource_input = self.make_labeled_input(controls, "Resource", "scoreboard")

        fetch_button = Button(text="Fetch", size_hint_x=None, width=110)
        fetch_button.bind(on_press=lambda _button: self.fetch_resource())
        controls.add_widget(fetch_button)
        main.add_widget(controls)

        quick_buttons = BoxLayout(orientation="horizontal", size_hint_y=None, height=42, spacing=8)
        for label, resource in [
            ("scoreboard", "scoreboard"),
            ("teams", "teams"),
            ("Bills team", f"teams/{TARGET['team_slug']}"),
            ("news", "news"),
            ("game summary", f"summary?event={TARGET['event_id']}"),
        ]:
            button = Button(text=label)
            button.bind(on_press=lambda _button, value=resource: self.set_resource(value))
            quick_buttons.add_widget(button)
        main.add_widget(quick_buttons)

        self.url_label = Label(text="", size_hint_y=None, height=52, halign="left", valign="middle")
        self.url_label.bind(size=lambda label, _size: setattr(label, "text_size", label.size))
        main.add_widget(self.url_label)

        self.output = TextInput(
            text="",
            readonly=True,
            font_size=14,
            background_color=(0.08, 0.08, 0.08, 1),
            foreground_color=(0.95, 0.95, 0.95, 1),
            cursor_color=(0.95, 0.95, 0.95, 1),
        )
        main.add_widget(self.output)

        for input_box in [self.sport_input, self.league_input, self.resource_input]:
            input_box.bind(text=lambda *_args: self.update_url_preview())

        self.update_url_preview()
        Clock.schedule_once(lambda _dt: self.fetch_resource(), 0.2)

        return main

    def make_labeled_input(self, parent, label_text, default_text):
        group = BoxLayout(orientation="vertical", spacing=4)
        group.add_widget(Label(text=label_text, size_hint_y=None, height=24))
        input_box = TextInput(text=default_text, multiline=False, write_tab=False)
        group.add_widget(input_box)
        parent.add_widget(group)
        return input_box

    def get_url(self):
        return build_site_v2_url(
            self.sport_input.text,
            self.league_input.text,
            self.resource_input.text,
        )

    def update_url_preview(self):
        self.url_label.text = f"Built URL:\n{self.get_url()}"

    def set_resource(self, resource):
        self.resource_input.text = resource
        self.fetch_resource()

    def write_output(self, text):
        self.output.text = text

    def fetch_resource(self):
        url = self.get_url()
        resource = self.resource_input.text.strip().strip("/")
        self.update_url_preview()
        self.write_output(f"Fetching:\n{url}\n")

        try:
            data = fetch_json(url)
        except requests.RequestException as error:
            self.write_output(f"Request failed:\n{error}")
            return

        preview = render_site_v2_preview(resource, data)
        self.write_output(f"URL:\n{url}\n\n{preview}")


def run_cli_sampler():
    for endpoint_name, endpoint_url in ENDPOINTS.items():
        show_endpoint(endpoint_name, endpoint_url)


if __name__ == "__main__":
    NashTrackApp().run()











