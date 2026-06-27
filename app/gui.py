import contextlib
import calendar
import io
import json
import math
import queue
import sys
import threading
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from kivy.app import App
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Mesh, Rectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

from app.favorites import load_favorites, save_favorites, sort_with_favorites
from app.preferences import load_preferences, save_preferences
from app.ui_registry import DASHBOARD_MODULE_DEFINITIONS, DASHBOARD_MODULES, DEFAULT_DASHBOARD_MODULES
from api.espn_core_v2 import get_leagues, get_sports
from api.espn_site_v2 import build_url, get_resource
from api.openf1 import build_url as build_openf1_url, get_resource as get_openf1_resource, get_sessions as get_openf1_sessions


FALLBACK_SPORTS = ["football", "basketball", "baseball", "hockey"]
FALLBACK_LEAGUES = {
    "football": ["cfl", "college-football", "nfl", "ufl", "xfl"],
    "basketball": ["nba", "mens-college-basketball", "womens-college-basketball", "wnba"],
    "baseball": ["mlb", "college-baseball"],
    "hockey": ["nhl", "mens-college-hockey", "womens-college-hockey"],
}

DEFAULT_SPORT = "football"
DEFAULT_LEAGUE = "nfl"
DEFAULT_TEAM_SLUG = "buf"
DEFAULT_EVENT_ID = "401772988"
# Flip this back on when the hidden sidebar screens are ready to ship.
ENABLE_UNFINISHED_FEATURES = False
ENABLE_CALENDAR_FEATURE = True
ENABLE_API_EXPLORER = True
ENABLE_SETTINGS = True
ENABLE_POINTER_DEBUG_WINDOW = False
CALENDAR_DAY_CARD_HEIGHT = dp(224)
CALENDAR_DAY_CARD_SPACING = dp(6)

RESOURCES = {
    "Scoreboard": "scoreboard",
    "Teams": "teams",
    "Team details": "team",
    "News": "news",
}

SPORT_PRESETS = {
    "all": (DEFAULT_SPORT, DEFAULT_LEAGUE),
    "football": ("football", "nfl"),
    "basketball": ("basketball", "nba"),
    "baseball": ("baseball", "mlb"),
    "hockey": ("hockey", "nhl"),
    "soccer": ("soccer", "eng.1"),
    "f1": ("racing", "f1"),
}

CALENDAR_SPORTS = {
    "NFL": {
        "label": "NFL",
        "sport": "football",
        "league": "nfl",
        "color": [0.30, 0.62, 1.00, 1],
    },
    "NBA": {
        "label": "NBA",
        "sport": "basketball",
        "league": "nba",
        "color": [1.00, 0.55, 0.05, 1],
    },
    "MLB": {
        "label": "MLB",
        "sport": "baseball",
        "league": "mlb",
        "color": [0.48, 0.88, 0.72, 1],
    },
    "NHL": {
        "label": "NHL",
        "sport": "hockey",
        "league": "nhl",
        "color": [0.68, 0.52, 1.00, 1],
    },
    "EPL": {
        "label": "EPL",
        "sport": "soccer",
        "league": "eng.1",
        "color": [0.95, 0.78, 0.25, 1],
    },
    "F1": {
        "label": "F1",
        "sport": "racing",
        "league": "f1",
        "color": [1.00, 0.18, 0.22, 1],
    },
}

F1_SESSION_LABELS = {
    "FP1": "Practice 1",
    "FP2": "Practice 2",
    "FP3": "Practice 3",
    "SS": "Sprint Shootout",
    "SR": "Sprint Race",
    "Q": "Qualifying",
    "R": "Race",
}


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

    for event in events[:8]:
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

    for team_wrapper in teams[:15]:
        team = team_wrapper.get("team", {})
        abbreviation = team.get("abbreviation", "")
        display_name = team.get("displayName", "Unknown team")
        print(f"  {abbreviation:5} {display_name}")


def show_news(data):
    articles = data.get("articles", [])
    print(f"Articles found: {len(articles)}")

    for article in articles[:8]:
        headline = article.get("headline", "No headline")
        published = format_published(article.get("published", ""))
        description = article.get("description", "")
        print()
        print(headline)
        print(f"  Published: {published}")
        if description:
            print(f"  {description[:160]}...")


def show_summary(data):
    header = data.get("header", {})
    competitions = header.get("competitions", [])

    print(header.get("name", "Unknown summary"))
    if competitions:
        status = competitions[0].get("status", {}).get("type", {}).get("description", "")
        print(f"Status: {status}")

    boxscore = data.get("boxscore", {})
    teams = boxscore.get("teams", [])
    leaders = data.get("leaders", [])
    drives = data.get("drives", {})

    print(f"Boxscore teams: {len(teams)}")
    print(f"Leader sections: {len(leaders)}")
    if isinstance(drives, dict):
        print(f"Drive sections: {', '.join(drives.keys())}")


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


def get_league_logo_url(data):
    if not isinstance(data, dict):
        return ""

    for league in data.get("leagues", []):
        for logo in league.get("logos", []):
            href = logo.get("href", "")
            if href:
                return href

    return ""


def get_article_image_url(article):
    for image in article.get("images", []):
        url = image.get("url") or image.get("href")
        if url:
            return url

    links = article.get("links", {})
    if isinstance(links, dict):
        for link_group in links.values():
            if isinstance(link_group, dict):
                images = link_group.get("images", [])
                for image in images:
                    url = image.get("url") or image.get("href")
                    if url:
                        return url

    return ""


def get_article_url(article):
    links = article.get("links", {})
    if not isinstance(links, dict):
        return ""

    web_link = links.get("web", {})
    if isinstance(web_link, dict):
        return web_link.get("href", "")

    return ""


def format_published(value):
    if not value:
        return "Published time unavailable"

    return value.replace("T", " ").replace("Z", " UTC")


def hex_to_rgba(value, alpha=1):
    if not value:
        return [0.95, 0.98, 1, alpha]

    value = value.strip().lstrip("#")
    if len(value) != 6:
        return [0.95, 0.98, 1, alpha]

    try:
        return [
            int(value[0:2], 16) / 255,
            int(value[2:4], 16) / 255,
            int(value[4:6], 16) / 255,
            alpha,
        ]
    except ValueError:
        return [0.95, 0.98, 1, alpha]


def get_team_logo(team):
    logo = team.get("logo", "")
    if logo:
        return logo

    for item in team.get("logos", []):
        href = item.get("href", "")
        if href:
            return href

    return ""


def parse_espn_datetime(value):
    if not value:
        return None

    try:
        clean_value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(clean_value).astimezone()
    except ValueError:
        return None


def format_event_datetime(value):
    parsed = parse_espn_datetime(value)
    if not parsed:
        return "time unavailable"

    return parsed.strftime("%b %d, %-I:%M %p") if sys.platform != "win32" else parsed.strftime("%b %d, %#I:%M %p")


def is_event_relevant(event, now=None):
    status = event.get("status", {})
    state = status.get("type", {}).get("state", "")
    if state == "in":
        return True

    event_time = parse_espn_datetime(event.get("date"))
    if not event_time:
        return state == "post"

    now = now or datetime.now().astimezone()
    if state == "pre":
        return now <= event_time <= now + timedelta(hours=24)

    # Keep completed games if ESPN only returns a completed event for this feed.
    return state == "post"


def is_live_or_upcoming_event(event, now=None):
    status = event.get("status", {})
    state = status.get("type", {}).get("state", "")
    if state == "in":
        return True

    if state != "pre":
        return False

    event_time = parse_espn_datetime(event.get("date"))
    if not event_time:
        return False

    now = now or datetime.now().astimezone()
    return now <= event_time <= now + timedelta(hours=24)


def format_game_clock(status, event_date=None):
    if not isinstance(status, dict):
        return "Status unavailable"

    status_type = status.get("type", {})
    state = status_type.get("state", "")
    description = status_type.get("description") or status_type.get("detail") or status_type.get("shortDetail") or "Status unavailable"
    period = status.get("period")
    display_clock = status.get("displayClock", "")

    if state == "in":
        if period and display_clock:
            return f"Q{period} - {display_clock} left"
        if period:
            return f"Q{period}"
        if display_clock:
            return f"{display_clock} left"

    if state == "pre":
        return f"Starts at: {format_event_datetime(event_date)}"

    if state == "post":
        return "Game ended at: time unavailable"

    return description


class StarButton(ButtonBehavior, Widget):
    def __init__(self, filled=False, **kwargs):
        super().__init__(**kwargs)
        self.filled = filled
        self.bind(pos=lambda *_args: self.redraw())
        self.bind(size=lambda *_args: self.redraw())
        self.redraw()

    def set_filled(self, filled):
        self.filled = filled
        self.redraw()

    def get_points(self):
        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2
        outer_radius = min(self.width, self.height) * 0.34
        inner_radius = outer_radius * 0.45
        points = []

        for index in range(10):
            angle = math.radians(-90 + index * 36)
            radius = outer_radius if index % 2 == 0 else inner_radius
            points.extend([
                center_x + math.cos(angle) * radius,
                center_y + math.sin(angle) * radius,
            ])

        return points

    def redraw(self):
        points = self.get_points()
        self.canvas.clear()

        with self.canvas:
            Color(1.0, 0.78, 0.18, 1)

            if self.filled:
                vertices = [
                    self.x + self.width / 2,
                    self.y + self.height / 2,
                    0,
                    0,
                ]
                for index in range(0, len(points), 2):
                    vertices.extend([points[index], points[index + 1], 0, 0])
                vertices.extend([points[0], points[1], 0, 0])
                Mesh(
                    vertices=vertices,
                    indices=list(range(len(vertices) // 4)),
                    mode="triangle_fan",
                )

            Line(points=points + points[:2], width=1.4)


class FavoriteDropdown(BoxLayout):
    def __init__(self, values, text, favorite_key, app_ref, on_select=None, **kwargs):
        super().__init__(orientation="horizontal", **kwargs)
        self.values = list(values)
        self.text = text
        self.favorite_key = favorite_key
        self.app_ref = app_ref
        self.on_select = on_select

        self.button = Button(text=text)
        self.button.bind(on_press=lambda _button: self.open_dropdown())
        self.add_widget(self.button)

    def set_text(self, value):
        self.text = value
        self.button.text = value

    def set_values(self, values):
        self.values = list(values)

    def open_dropdown(self):
        dropdown = DropDown()

        for value in self.values:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=44)

            star_button = StarButton(
                filled=self.app_ref.is_favorite(self.favorite_key, value),
                size_hint_x=None,
                width=44,
            )
            value_button = Button(text=value)

            star_button.bind(
                on_press=lambda _button, selected=value: self.toggle_star(selected, dropdown)
            )
            value_button.bind(
                on_press=lambda _button, selected=value: self.select_value(selected, dropdown)
            )

            row.add_widget(star_button)
            row.add_widget(value_button)
            dropdown.add_widget(row)

        dropdown.open(self.button)

    def select_value(self, value, dropdown):
        self.set_text(value)
        dropdown.dismiss()

        if self.on_select:
            self.on_select()

    def toggle_star(self, value, dropdown):
        self.app_ref.toggle_favorite_value(self.favorite_key, value)
        self.set_values(self.app_ref.sort_values(self.values, self.favorite_key))
        dropdown.dismiss()
        self.open_dropdown()


class LargeGameCard(BoxLayout):
    league = StringProperty("")
    logo_url = StringProperty("")
    main_text = StringProperty("")
    status = StringProperty("")
    stats_text = StringProperty("")
    accent = ListProperty([0.20, 0.52, 1.0, 1])


class SmallEventCard(ButtonBehavior, BoxLayout):
    event_id = StringProperty("")
    sport_slug = StringProperty("")
    league_slug = StringProperty("")
    title = StringProperty("")
    main_text = StringProperty("")
    date_text = StringProperty("")
    time_text = StringProperty("")
    away_abbreviation = StringProperty("")
    away_logo = StringProperty("")
    away_score = StringProperty("-")
    away_color = ListProperty([0.95, 0.98, 1, 1])
    home_abbreviation = StringProperty("")
    home_logo = StringProperty("")
    home_score = StringProperty("-")
    home_color = ListProperty([0.95, 0.98, 1, 1])
    weather_icon = StringProperty("")
    weather_text = StringProperty("")
    venue_text = StringProperty("")
    detail_payload = ObjectProperty(None, allownone=True)

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, "open_event_card_overlay"):
            app.open_event_card_overlay(self)


class F1SessionCard(ButtonBehavior, BoxLayout):
    event_id = StringProperty("")
    status_label = StringProperty("")
    grand_prix = StringProperty("Formula 1")
    session_name = StringProperty("Session")
    session_code = StringProperty("")
    time_text = StringProperty("")
    circuit_text = StringProperty("")
    location_text = StringProperty("")
    timeline_text = StringProperty("")
    detail_payload = ObjectProperty(None, allownone=True)
    accent = ListProperty([1.00, 0.18, 0.22, 1])

    def on_release(self):
        app = App.get_running_app()
        if hasattr(app, "open_event_card_overlay"):
            app.open_event_card_overlay(self)


class LoadingSpinner(Widget):
    active = BooleanProperty(False)
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._spin_event = None
        self.bind(pos=lambda *_args: self.redraw())
        self.bind(size=lambda *_args: self.redraw())
        self.bind(angle=lambda *_args: self.redraw())
        self.bind(active=lambda *_args: self.update_spin_state())
        self.update_spin_state()
        self.redraw()

    def update_spin_state(self):
        if self.active and self._spin_event is None:
            self._spin_event = Clock.schedule_interval(self.spin, 1 / 30)
        elif not self.active and self._spin_event is not None:
            self._spin_event.cancel()
            self._spin_event = None
        self.redraw()

    def spin(self, _dt):
        self.angle = (self.angle + 12) % 360

    def on_parent(self, _widget, parent):
        if parent is None and self._spin_event is not None:
            self._spin_event.cancel()
            self._spin_event = None

    def redraw(self):
        self.canvas.clear()
        if not self.active:
            return

        unit = min(self.width, self.height)
        if unit <= 0:
            return

        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        radius = unit * 0.34
        points = []
        for index in range(22):
            angle = math.radians(self.angle + index * 10)
            points.extend([
                cx + math.cos(angle) * radius,
                cy + math.sin(angle) * radius,
            ])

        with self.canvas:
            Color(0.30, 0.62, 1.0, 0.22)
            Line(circle=(cx, cy, radius), width=max(1.0, unit * 0.07))
            Color(0.72, 0.92, 1.0, 1)
            Line(points=points, width=max(1.2, unit * 0.08))


class WeatherIcon(Widget):
    icon_type = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=lambda *_args: self.redraw())
        self.bind(size=lambda *_args: self.redraw())
        self.bind(icon_type=lambda *_args: self.redraw())
        self.redraw()

    def redraw(self):
        self.canvas.clear()
        if not self.icon_type:
            return

        x = self.x
        y = self.y
        width = self.width
        height = self.height
        unit = min(width, height)
        cx = x + width / 2
        cy = y + height / 2

        with self.canvas:
            if self.icon_type == "sun":
                Color(0.98, 0.78, 0.24, 1)
                radius = unit * 0.22
                Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2))
                for angle in range(0, 360, 45):
                    radians = math.radians(angle)
                    inner = unit * 0.30
                    outer = unit * 0.42
                    Line(
                        points=[
                            cx + math.cos(radians) * inner,
                            cy + math.sin(radians) * inner,
                            cx + math.cos(radians) * outer,
                            cy + math.sin(radians) * outer,
                        ],
                        width=1.2,
                    )
            elif self.icon_type == "rain":
                self.draw_cloud(cx, cy, unit)
                Color(0.30, 0.62, 1.0, 1)
                for offset in (-0.18, 0, 0.18):
                    Line(
                        points=[
                            cx + unit * offset,
                            y + unit * 0.36,
                            cx + unit * (offset - 0.06),
                            y + unit * 0.14,
                        ],
                        width=1.2,
                    )
            elif self.icon_type == "snow":
                self.draw_cloud(cx, cy, unit)
                Color(0.78, 0.92, 1.0, 1)
                for offset in (-0.16, 0.16):
                    Line(points=[cx + unit * offset, y + unit * 0.12, cx + unit * offset, y + unit * 0.30], width=1.1)
                    Line(points=[cx + unit * (offset - 0.06), y + unit * 0.21, cx + unit * (offset + 0.06), y + unit * 0.21], width=1.1)
            elif self.icon_type == "storm":
                self.draw_cloud(cx, cy, unit)
                Color(1.0, 0.78, 0.18, 1)
                points = [
                    cx - unit * 0.02, y + unit * 0.36,
                    cx - unit * 0.12, y + unit * 0.12,
                    cx + unit * 0.03, y + unit * 0.18,
                    cx - unit * 0.02, y,
                    cx + unit * 0.18, y + unit * 0.26,
                    cx + unit * 0.04, y + unit * 0.22,
                ]
                Line(points=points, width=1.4)
            else:
                self.draw_cloud(cx, cy, unit)

    def draw_cloud(self, cx, cy, unit):
        Color(0.70, 0.80, 0.92, 1)
        Ellipse(pos=(cx - unit * 0.34, cy - unit * 0.08), size=(unit * 0.34, unit * 0.28))
        Ellipse(pos=(cx - unit * 0.16, cy + unit * 0.02), size=(unit * 0.36, unit * 0.34))
        Ellipse(pos=(cx + unit * 0.04, cy - unit * 0.08), size=(unit * 0.34, unit * 0.28))
        Rectangle(pos=(cx - unit * 0.30, cy - unit * 0.06), size=(unit * 0.62, unit * 0.20))


class CarouselMessageCard(BoxLayout):
    title = StringProperty("")
    message = StringProperty("")


class NewsCard(ButtonBehavior, BoxLayout):
    opening = BooleanProperty(False)
    flash_alpha = NumericProperty(0)
    url = StringProperty("")
    headline = StringProperty("")
    published = StringProperty("")
    description = StringProperty("")
    image_url = StringProperty("")

    def on_release(self):
        self.open_url()

    def open_url(self):
        if self.url:
            import webbrowser

            app = App.get_running_app()
            if hasattr(app, "show_busy_overlay"):
                app.show_busy_overlay("Retrieving article...")
                Clock.schedule_once(lambda _dt: app.hide_busy_overlay(), 0.7)
            webbrowser.open(self.url)


class F1RaceDetailScreen(BoxLayout):
    race_title = StringProperty("Loading race")
    race_subtitle = StringProperty("OpenF1")
    ended_text = StringProperty("Retrieving data...")
    p1_driver = StringProperty("--")
    p1_team = StringProperty("--")
    p1_headshot = StringProperty("")
    p1_color = ListProperty([1, 0.82, 0.15, 1])
    p2_driver = StringProperty("--")
    p2_team = StringProperty("--")
    p2_headshot = StringProperty("")
    p2_color = ListProperty([0.75, 0.78, 0.85, 1])
    p3_driver = StringProperty("--")
    p3_team = StringProperty("--")
    p3_headshot = StringProperty("")
    p3_color = ListProperty([0.85, 0.45, 0.20, 1])
    classification_text = StringProperty("Loading classification...")
    weather_text = StringProperty("Loading weather...")
    race_control_text = StringProperty("Loading race control...")

    def load_latest_completed_race(self):
        now = datetime.now().astimezone()
        self.openf1_errors = {}
        session = self.get_latest_completed_race_session(now)
        if not session:
            self.show_error("No completed OpenF1 Race session found.")
            return

        session_key = session.get("session_key")
        if not session_key:
            self.show_error("Latest race did not include a session key.")
            return

        self.openf1_errors = {}
        meetings = self.fetch_openf1_list("meetings", {"meeting_key": session.get("meeting_key")})
        meeting = meetings[0] if meetings else {}
        self.apply_session_header(session, meeting)
        positions = self.fetch_openf1_list("position", {"session_key": session_key})
        drivers = self.fetch_openf1_list("drivers", {"session_key": session_key})
        weather = self.fetch_openf1_list("weather", {"session_key": session_key})
        race_control = self.fetch_openf1_list("race_control", {"session_key": session_key})

        driver_map = {str(driver.get("driver_number")): driver for driver in drivers}
        final_positions = self.get_final_positions(positions)
        self.apply_winners(final_positions, driver_map)
        self.classification_text = self.format_error_or("position", self.format_classification(final_positions, driver_map))
        if "drivers" in self.openf1_errors:
            self.classification_text = f"{self.classification_text}\n\nDriver metadata error: {self.openf1_errors['drivers']}"
        self.weather_text = self.format_error_or("weather", self.format_weather(weather))
        self.race_control_text = self.format_error_or("race_control", self.format_race_control(race_control))

    def close(self):
        app = App.get_running_app()
        popup = getattr(app, "event_detail_popup", None)
        if popup is not None:
            popup.dismiss()

    def get_latest_completed_race_session(self, now):
        sessions = []
        for year in (now.year, now.year - 1):
            sessions.extend(self.fetch_openf1_list("sessions", {
                "session_type": "Race",
                "year": year,
            }))

        completed = []
        for session in sessions:
            end_time = parse_espn_datetime(session.get("date_end"))
            if end_time and end_time < now:
                completed.append((end_time, session))

        if not completed:
            return None

        completed.sort(key=lambda item: item[0], reverse=True)
        return completed[0][1]

    def fetch_openf1_list(self, endpoint, params):
        try:
            data = get_openf1_resource(endpoint, params)
        except requests.HTTPError as error:
            response = getattr(error, "response", None)
            if getattr(response, "status_code", None) != 404:
                self.openf1_errors[endpoint] = str(error)
            return []
        except requests.RequestException:
            self.openf1_errors[endpoint] = "OpenF1 request failed."
            return []
        return data if isinstance(data, list) else []

    def format_error_or(self, endpoint, fallback_text):
        error = self.openf1_errors.get(endpoint)
        if error:
            return f"Error loading OpenF1 {endpoint}: {error}"
        return fallback_text

    def apply_session_header(self, session, meeting=None):
        meeting = meeting or {}
        country = session.get("country_name", "")
        session_name = session.get("session_name") or "Race"
        circuit = session.get("circuit_short_name", "")
        location = session.get("location", "")
        start_time = parse_espn_datetime(session.get("date_start"))
        end_time = parse_espn_datetime(session.get("date_end"))
        meeting_name = meeting.get("meeting_name") or meeting.get("meeting_official_name") or ""

        race_name = meeting_name or (f"{country} Grand Prix" if country else "Formula 1")
        self.race_title = f"{race_name} - {session_name}"
        self.race_subtitle = " | ".join(part for part in [circuit, location, country, self.format_time_range(start_time, end_time)] if part)
        self.ended_text = f"Race ended at {self.format_clock(end_time)} on {self.format_date(end_time)}"

    def format_time_range(self, start_time, end_time):
        if not start_time or not end_time:
            return ""
        return f"{self.format_clock(start_time)} - {self.format_clock(end_time)}"

    def format_clock(self, value):
        if not value:
            return "time unavailable"
        return value.strftime("%#I:%M %p") if sys.platform == "win32" else value.strftime("%-I:%M %p")

    def format_date(self, value):
        if not value:
            return "date unavailable"
        return value.strftime("%b %d, %Y")

    def get_final_positions(self, positions):
        latest_by_driver = {}
        for row in positions:
            driver_number = str(row.get("driver_number", ""))
            if not driver_number:
                continue

            row_date = parse_espn_datetime(row.get("date"))
            previous = latest_by_driver.get(driver_number)
            previous_date = parse_espn_datetime(previous.get("date")) if previous else None
            if previous is None or (row_date and (previous_date is None or row_date >= previous_date)):
                latest_by_driver[driver_number] = row

        rows = list(latest_by_driver.values())
        rows.sort(key=lambda row: self.safe_int(row.get("position"), 999))
        return rows

    def safe_int(self, value, fallback):
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def apply_winners(self, final_positions, driver_map):
        winner_defaults = [
            ("p1", [1, 0.82, 0.15, 1]),
            ("p2", [0.75, 0.78, 0.85, 1]),
            ("p3", [0.85, 0.45, 0.20, 1]),
        ]
        for index, (prefix, fallback_color) in enumerate(winner_defaults):
            row = final_positions[index] if index < len(final_positions) else {}
            driver = driver_map.get(str(row.get("driver_number", "")), {})
            setattr(self, f"{prefix}_driver", self.get_driver_name(driver, row))
            setattr(self, f"{prefix}_team", driver.get("team_name", "Team unavailable"))
            setattr(self, f"{prefix}_headshot", driver.get("headshot_url", "") or "")
            setattr(self, f"{prefix}_color", hex_to_rgba(driver.get("team_colour", ""), 1) if driver.get("team_colour") else fallback_color)

    def get_driver_name(self, driver, row):
        return (
            driver.get("full_name")
            or driver.get("broadcast_name")
            or driver.get("last_name")
            or f"Driver {row.get('driver_number', '--')}"
        )

    def format_classification(self, final_positions, driver_map):
        if not final_positions:
            return "Final position data not posted yet."

        lines = ["POS   DRIVER                     TEAM"]
        for row in final_positions:
            position = row.get("position", "?")
            driver = driver_map.get(str(row.get("driver_number", "")), {})
            name = self.get_driver_name(driver, row)
            team = driver.get("team_name", "Team unavailable")
            lines.append(f"P{position:<4} {name[:24]:<24} {team[:22]}")
        return "\n".join(lines)

    def format_weather(self, weather):
        if not weather:
            return "Weather data not posted yet."

        latest = sorted(weather, key=lambda row: parse_espn_datetime(row.get("date")) or datetime.min.replace(tzinfo=timezone.utc))[-1]
        sample_time = format_event_datetime(latest.get("date"))
        return "\n".join([
            f"Sample: {sample_time}",
            f"Air: {latest.get('air_temperature', '?')} C",
            f"Track: {latest.get('track_temperature', '?')} C",
            f"Humidity: {latest.get('humidity', '?')}%",
            f"Rainfall: {latest.get('rainfall', '?')}",
            f"Wind: {latest.get('wind_speed', '?')} m/s",
        ])

    def format_race_control(self, messages):
        if not messages:
            return "Race control messages not posted yet."

        latest_messages = sorted(
            messages,
            key=lambda row: parse_espn_datetime(row.get("date")) or datetime.min.replace(tzinfo=timezone.utc),
        )[-5:]
        lines = []
        for message in latest_messages:
            timestamp = format_event_datetime(message.get("date"))
            category = message.get("category", "Message")
            text = message.get("message", "")
            lines.append(f"{timestamp}\n{category}: {text}")
        return "\n\n".join(lines)

    def show_error(self, message):
        self.race_title = "F1 Race Detail"
        self.race_subtitle = "OpenF1"
        self.ended_text = "Unable to load"
        self.classification_text = message
        self.weather_text = "No weather loaded."
        self.race_control_text = "No race control loaded."


class CalendarDot(Widget):
    dot_color = ListProperty([0.30, 0.62, 1, 1])


class CalendarDay(ButtonBehavior, BoxLayout):
    day_text = StringProperty("")
    overflow_text = StringProperty("")
    event_date = StringProperty("")
    is_today = BooleanProperty(False)
    bg_color = ListProperty([0.035, 0.060, 0.105, 1])
    border_color = ListProperty([0.08, 0.12, 0.18, 1])

    def on_release(self):
        app = App.get_running_app()
        if not getattr(app, "calendar_feature_enabled", False):
            return

        if not self.event_date:
            return

        if hasattr(app, "open_calendar_day"):
            app.open_calendar_day(self.event_date)


class CalendarEventCard(ButtonBehavior, BoxLayout):
    event_id = StringProperty("")
    sport = StringProperty("")
    sport_label = StringProperty("")
    title = StringProperty("")
    time_text = StringProperty("")
    status_text = StringProperty("")
    venue_text = StringProperty("")
    weather_icon = StringProperty("")
    weather_text = StringProperty("")
    away_name = StringProperty("")
    away_abbreviation = StringProperty("")
    away_logo = StringProperty("")
    away_color = ListProperty([0.95, 0.98, 1, 1])
    home_name = StringProperty("")
    home_abbreviation = StringProperty("")
    home_logo = StringProperty("")
    home_color = ListProperty([0.95, 0.98, 1, 1])
    session_text = StringProperty("")
    broadcast_text = StringProperty("")
    sport_color = ListProperty([0.30, 0.62, 1, 1])
    is_f1 = BooleanProperty(False)

    def on_release(self):
        app = App.get_running_app()
        if not getattr(app, "unfinished_features_enabled", False):
            return

        if self.event_id and self.sport != "F1":
            if hasattr(app, "open_game_detail"):
                app.open_game_detail(self.event_id)


class CalendarDayEventCard(ButtonBehavior, BoxLayout):
    event_id = StringProperty("")
    sport = StringProperty("")
    sport_label = StringProperty("")
    title = StringProperty("")
    time_text = StringProperty("")
    status_text = StringProperty("")
    venue_text = StringProperty("")
    weather_icon = StringProperty("")
    weather_text = StringProperty("")
    away_name = StringProperty("")
    away_abbreviation = StringProperty("")
    away_logo = StringProperty("")
    away_color = ListProperty([0.95, 0.98, 1, 1])
    home_name = StringProperty("")
    home_abbreviation = StringProperty("")
    home_logo = StringProperty("")
    home_color = ListProperty([0.95, 0.98, 1, 1])
    session_text = StringProperty("")
    broadcast_text = StringProperty("")
    sport_color = ListProperty([0.30, 0.62, 1, 1])
    is_f1 = BooleanProperty(False)

    def on_release(self):
        app = App.get_running_app()
        if not getattr(app, "unfinished_features_enabled", False):
            return

        if self.event_id and self.sport != "F1":
            if hasattr(app, "open_game_detail"):
                app.open_game_detail(self.event_id)


class CalendarDayPopup(Popup):
    title_text = StringProperty("")
    subtitle_text = StringProperty("")


class SummaryMetric(BoxLayout):
    value = StringProperty("")
    label = StringProperty("")
    accent = ListProperty([0.30, 0.62, 1.00, 1])


class PointerDebugReporter:
    def __init__(self):
        self.events = queue.Queue()
        self.ready = False

    def start(self):
        thread = threading.Thread(target=self.run_window, daemon=True)
        thread.start()

    def log(self, message):
        if self.ready:
            self.events.put(message)

    def run_window(self):
        try:
            import tkinter as tk
        except ImportError:
            return

        root = tk.Tk()
        root.title("Nash Track Pointer Debug")
        root.geometry("560x360+40+40")
        root.attributes("-topmost", True)

        header = tk.Label(
            root,
            text="Pointer debug: move/click/drag inside the Kivy app",
            anchor="w",
        )
        header.pack(fill="x", padx=8, pady=(8, 2))

        text = tk.Text(root, wrap="word", height=18)
        text.pack(fill="both", expand=True, padx=8, pady=8)
        text.insert("end", "Waiting for pointer events...\n")
        text.configure(state="disabled")
        self.ready = True

        def pump():
            drained = False
            while True:
                try:
                    message = self.events.get_nowait()
                except queue.Empty:
                    break

                drained = True
                text.configure(state="normal")
                text.insert("end", message + "\n")
                text.see("end")
                text.configure(state="disabled")

            if drained:
                lines = int(text.index("end-1c").split(".")[0])
                if lines > 220:
                    text.configure(state="normal")
                    text.delete("1.0", "80.0")
                    text.configure(state="disabled")

            root.after(80, pump)

        root.after(80, pump)
        root.mainloop()


class ZoneDashboardScreen(BoxLayout):
    active_view = StringProperty("home")
    active_sport = StringProperty("all")
    settings_version = NumericProperty(0)
    debug_open = BooleanProperty(False)
    busy = BooleanProperty(False)
    busy_text = StringProperty("Retrieving data...")

    def set_sport(self, sport):
        app = App.get_running_app()
        if sport != "all" and not getattr(app, "unfinished_features_enabled", False):
            return

        self.active_view = "home"
        self.active_sport = sport
        if hasattr(app, "apply_sport_preset"):
            app.apply_sport_preset(sport)
        if hasattr(app, "show_debug_for_current_view"):
            app.show_debug_for_current_view()

    def show_settings(self):
        app = App.get_running_app()
        if not getattr(app, "settings_enabled", False):
            return

        self.active_view = "settings"
        if hasattr(app, "show_debug_for_current_view"):
            app.show_debug_for_current_view()

    def show_calendar(self):
        app = App.get_running_app()
        if not getattr(app, "calendar_feature_enabled", False):
            return

        self.active_view = "calendar"
        if hasattr(app, "build_calendar_view"):
            app.build_calendar_view()
        if hasattr(app, "show_debug_for_current_view"):
            app.show_debug_for_current_view()

    def show_api(self):
        app = App.get_running_app()
        if not getattr(app, "api_explorer_enabled", False):
            return

        self.active_view = "api"
        if hasattr(app, "show_debug_for_current_view"):
            app.show_debug_for_current_view()

    def show_favorites(self):
        app = App.get_running_app()
        if not getattr(app, "unfinished_features_enabled", False):
            return

        self.active_view = "favorites"
        if hasattr(app, "show_debug_for_current_view"):
            app.show_debug_for_current_view()

    def refresh(self):
        app = App.get_running_app()
        if self.active_view == "api" and hasattr(app, "fetch_resource"):
            app.fetch_resource()
        elif hasattr(app, "refresh_dashboard"):
            app.refresh_dashboard()

    def toggle_debug(self):
        app = App.get_running_app()
        if not getattr(app, "unfinished_features_enabled", False):
            return

        if hasattr(app, "toggle_debug_panel"):
            app.toggle_debug_panel()

    def is_home_sport_enabled(self, sport, _settings_version):
        app = App.get_running_app()
        enabled = getattr(app, "home_sports", set())
        return sport in enabled

    def set_home_sport_enabled(self, sport, enabled):
        app = App.get_running_app()
        if hasattr(app, "set_calendar_sport_enabled"):
            app.set_calendar_sport_enabled(sport, enabled)

    def is_dashboard_module_enabled(self, module, _settings_version):
        app = App.get_running_app()
        enabled = getattr(app, "dashboard_modules", set())
        return module in enabled

    def set_dashboard_module_enabled(self, module, enabled):
        app = App.get_running_app()
        if hasattr(app, "set_dashboard_module_enabled"):
            app.set_dashboard_module_enabled(module, enabled)

    def on_touch_down(self, touch):
        app = App.get_running_app()
        if hasattr(app, "report_pointer_event"):
            app.report_pointer_event("CLICK", touch.pos, touch)
        if hasattr(app, "handle_dashboard_zone_touch_down") and app.handle_dashboard_zone_touch_down(touch):
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        app = App.get_running_app()
        if hasattr(app, "report_pointer_event"):
            app.report_pointer_event("DRAG", touch.pos, touch)
        if hasattr(app, "handle_dashboard_zone_touch_move") and app.handle_dashboard_zone_touch_move(touch):
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        app = App.get_running_app()
        if hasattr(app, "report_pointer_event"):
            app.report_pointer_event("RELEASE", touch.pos, touch)
        if hasattr(app, "handle_dashboard_zone_touch_up") and app.handle_dashboard_zone_touch_up(touch):
            return True
        return super().on_touch_up(touch)


class NashTrackApp(App):
    def build(self):
        self.title = "Nash Track"
        self.unfinished_features_enabled = ENABLE_UNFINISHED_FEATURES
        self.calendar_feature_enabled = ENABLE_CALENDAR_FEATURE
        self.api_explorer_enabled = ENABLE_API_EXPLORER
        self.settings_enabled = ENABLE_SETTINGS
        self.pointer_debug_enabled = ENABLE_POINTER_DEBUG_WINDOW
        self.pointer_debug_reporter = None
        self.last_pointer_move_log = 0
        self.last_pointer_drag_log = 0
        self.team_options = {}
        self.favorites = load_favorites()
        self.preferences = load_preferences()
        self.debug_expanded = False
        self.home_sports = self.load_home_sports_preference()
        self.dashboard_modules = self.load_dashboard_modules_preference()
        self.api_debug_payload = None
        self.dashboard_debug_payloads = {}
        self.live_game_slides = []
        self.live_game_index = 0
        self.now_next_items = []
        self.now_next_index = 0
        self.headline_articles = []
        self.headline_index = 0
        self.last_dashboard_drag_at = 0
        self.event_detail_popup = None
        self.busy_popup = None
        self.game_summary_cache = {}
        self.weather_cache = {}
        self.calendar_events = {}
        self.calendar_events_loaded = False
        self.openf1_sessions_cache = {}
        self.calendar_day_request_id = 0
        self.calendar_day_popup = None
        self.dashboard_today_stats = {
            "live": 0,
            "today": 0,
            "upcoming": 0,
            "next": "--",
        }

        Builder.load_file(str(PROJECT_ROOT / "dashboard.kv"))
        Builder.load_file(str(PROJECT_ROOT / "calendar_day.kv"))
        Builder.load_file(str(PROJECT_ROOT / "f1_race_detail.kv"))
        Builder.load_file(str(PROJECT_ROOT / "dashboard_zones.kv"))
        self.root_screen = ZoneDashboardScreen()
        self.setup_dashboard_widgets()
        self.setup_pointer_debug_window()

        self.update_url_preview()
        if self.api_explorer_enabled:
            Clock.schedule_once(lambda _dt: self.load_sports(), 0.2)
        Clock.schedule_once(lambda _dt: self.refresh_dashboard(), 0.6)

        return self.root_screen

    def setup_pointer_debug_window(self):
        if not self.pointer_debug_enabled:
            return

        self.pointer_debug_reporter = PointerDebugReporter()
        self.pointer_debug_reporter.start()
        Window.bind(mouse_pos=self.on_window_mouse_pos)
        Clock.schedule_once(lambda _dt: self.report_pointer_event("DEBUG", Window.mouse_pos), 0.5)

    def on_window_mouse_pos(self, _window, pos):
        now = time.monotonic()
        if now - self.last_pointer_move_log < 0.25:
            return

        self.last_pointer_move_log = now
        self.report_pointer_event("MOVE", pos)

    def report_pointer_event(self, action, pos, touch=None):
        if not self.pointer_debug_reporter:
            return

        if action == "DRAG":
            now = time.monotonic()
            if now - self.last_pointer_drag_log < 0.12:
                return
            self.last_pointer_drag_log = now

        x, y = pos
        section = self.get_pointer_section(pos)
        widget_hint = self.get_pointer_widget_hint(pos)
        touch_info = ""
        if touch is not None:
            button = getattr(touch, "button", "")
            if button:
                touch_info = f" button={button}"

        self.pointer_debug_reporter.log(
            f"{datetime.now():%H:%M:%S.%f} {action:<7} x={x:>6.1f} y={y:>6.1f} section={section} widget={widget_hint}{touch_info}"
        )

    def get_pointer_section(self, pos):
        if not hasattr(self, "root_screen"):
            return "no root"

        ids = self.root_screen.ids
        sections = [
            ("Top Headlines", "headlines_zone"),
            ("Now / Next", "now_next_zone"),
            ("Today", "today_summary"),
            ("Right Calendar", "calendar_grid"),
            ("Top Headlines cards", "headline_cards"),
            ("Now / Next cards", "live_games"),
            ("Calendar Tab", "main_calendar_grid"),
            ("API Controls", "api_controls"),
            ("API Preview", "api_preview"),
            ("Game Detail", "game_detail_body"),
            ("Settings", "settings_body"),
            ("Favorites", "favorites_main"),
        ]

        for label, widget_id in sections:
            widget = ids.get(widget_id)
            if widget and widget.opacity > 0 and not widget.disabled and widget.collide_point(*pos):
                return label

        if self.root_screen.collide_point(*pos):
            return f"{self.root_screen.active_view} view / unknown child"
        return "outside app"

    def get_dashboard_zone_at_pos(self, pos):
        if not hasattr(self, "root_screen") or self.root_screen.active_view != "home":
            return None

        ids = self.root_screen.ids
        for zone, widget_id in (("headlines", "headlines_zone"), ("now_next", "now_next_zone")):
            widget = ids.get(widget_id)
            if widget and not widget.disabled and widget.opacity > 0 and widget.collide_point(*pos):
                return zone
        return None

    def handle_dashboard_zone_touch_down(self, touch):
        button = getattr(touch, "button", "")
        zone = self.get_dashboard_zone_at_pos(touch.pos)
        if zone is None:
            return False

        if button in ("scrollup", "scrolldown"):
            direction = -1 if button == "scrollup" else 1
            self.scroll_dashboard_zone(zone, direction)
            return True

        touch.ud["dashboard_zone"] = zone
        touch.ud["dashboard_zone_last_y"] = touch.y
        touch.ud["dashboard_zone_moved"] = False
        touch.ud["dashboard_zone_start_pos"] = tuple(touch.pos)
        return False

    def handle_dashboard_zone_touch_move(self, touch):
        zone = touch.ud.get("dashboard_zone")
        if not zone:
            return False

        last_y = touch.ud.get("dashboard_zone_last_y", touch.y)
        delta = touch.y - last_y
        threshold = dp(34)
        if abs(delta) >= threshold:
            direction = -1 if delta > 0 else 1
            if self.scroll_dashboard_zone(zone, direction):
                touch.ud["dashboard_zone_last_y"] = touch.y
                touch.ud["dashboard_zone_moved"] = True
                self.last_dashboard_drag_at = time.monotonic()
        return True

    def handle_dashboard_zone_touch_up(self, touch):
        zone = touch.ud.pop("dashboard_zone", None)
        moved = touch.ud.pop("dashboard_zone_moved", False)
        touch.ud.pop("dashboard_zone_last_y", None)
        start_pos = touch.ud.pop("dashboard_zone_start_pos", touch.pos)
        if zone == "now_next" and not moved and self.is_same_tap(start_pos, touch.pos):
            card = self.get_now_next_card_at_pos(touch.pos)
            if card is not None:
                self.log_pointer_debug(f"OPEN overlay card={card.__class__.__name__} title={getattr(card, 'title', '')}")
                self.open_event_card_overlay(card, suppress_drag_guard=True)
                return True
            self.log_pointer_debug("NO CARD under Now / Next tap")
        return bool(zone and moved)

    def scroll_dashboard_zone(self, zone, direction):
        if zone == "headlines":
            return self.scroll_headline_cards(direction)
        if zone == "now_next":
            return self.scroll_now_next_cards(direction)
        return False

    def is_same_tap(self, start_pos, end_pos):
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        return (dx * dx + dy * dy) <= dp(12) * dp(12)

    def get_now_next_card_at_pos(self, pos):
        if not hasattr(self, "live_carousel_body"):
            return None

        for child in self.live_carousel_body.children:
            if isinstance(child, (SmallEventCard, F1SessionCard, CarouselMessageCard)) and child.collide_point(*pos):
                return child
        return None

    def log_pointer_debug(self, message):
        if self.pointer_debug_reporter:
            self.pointer_debug_reporter.log(f"{datetime.now():%H:%M:%S.%f} DEBUG   {message}")

    def get_pointer_widget_hint(self, pos):
        if not hasattr(self, "root_screen"):
            return "-"

        matches = []
        for widget_id, widget in self.root_screen.ids.items():
            try:
                if widget.opacity > 0 and not widget.disabled and widget.collide_point(*pos):
                    matches.append(widget_id)
            except AttributeError:
                continue

        if not matches:
            return "-"
        return ">".join(matches[:5])

    def load_home_sports_preference(self):
        saved_sports = set(self.preferences.get("home_sports", []))
        known_sports = set(CALENDAR_SPORTS.keys())
        clean_sports = saved_sports & known_sports
        return clean_sports or {"NFL", "F1"}

    def load_dashboard_modules_preference(self):
        saved_modules = set(self.preferences.get("dashboard_modules", []))
        known_modules = set(DASHBOARD_MODULES.keys())
        clean_modules = saved_modules & known_modules
        return clean_modules or set(DEFAULT_DASHBOARD_MODULES)

    def save_home_sports_preference(self):
        self.preferences["home_sports"] = [
            sport_key for sport_key in CALENDAR_SPORTS if sport_key in self.home_sports
        ]
        save_preferences(self.preferences)

    def save_dashboard_modules_preference(self):
        self.preferences["dashboard_modules"] = [
            module for module in DASHBOARD_MODULES if module in self.dashboard_modules
        ]
        save_preferences(self.preferences)

    def make_settings_toggle_row(self, label_text, active, on_active):
        row = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(8))
        row.add_widget(Label(
            text=label_text,
            color=(0.88, 0.93, 1, 1),
            font_size="14sp",
            halign="left",
            valign="middle",
            text_size=(dp(220), dp(32)),
        ))
        checkbox = CheckBox(size_hint_x=None, width=dp(36), active=active)
        checkbox.bind(active=lambda _checkbox, enabled: on_active(enabled))
        row.add_widget(checkbox)
        return row

    def setup_settings_panel(self):
        ids = self.root_screen.ids

        sports_grid = ids.get("home_sports_settings")
        if sports_grid:
            sports_grid.clear_widgets()
            sports_grid.cols = 2
            sports_grid.height = dp(102)
            for sport_key, config in CALENDAR_SPORTS.items():
                sports_grid.add_widget(self.make_settings_toggle_row(
                    f"{config['label']} feed",
                    sport_key in self.home_sports,
                    lambda enabled, key=sport_key: self.set_calendar_sport_enabled(key, enabled),
                ))

        modules_grid = ids.get("dashboard_modules_settings")
        if modules_grid:
            modules_grid.clear_widgets()
            modules_grid.cols = 2
            modules_grid.height = dp(68)
            for module in DASHBOARD_MODULE_DEFINITIONS:
                modules_grid.add_widget(self.make_settings_toggle_row(
                    module.label,
                    module.id in self.dashboard_modules,
                    lambda enabled, module_id=module.id: self.set_dashboard_module_enabled(module_id, enabled),
                ))

    def setup_dashboard_widgets(self):
        ids = self.root_screen.ids

        self.setup_home_dashboard()

        controls_box = ids.api_controls
        controls_box.clear_widgets()
        controls_box.cols = 1

        controls = BoxLayout(orientation="horizontal", size_hint_y=None, height=66, spacing=5)
        self.sport_dropdown = self.make_labeled_dropdown(
            controls,
            "Sport",
            DEFAULT_SPORT,
            FALLBACK_SPORTS,
            "sports",
        )
        self.league_dropdown = self.make_labeled_dropdown(
            controls,
            "League",
            DEFAULT_LEAGUE,
            FALLBACK_LEAGUES[DEFAULT_SPORT],
            "leagues",
        )
        self.resource_dropdown = self.make_labeled_dropdown(
            controls,
            "Resource",
            "Scoreboard",
            list(RESOURCES.keys()),
            "resources",
        )
        self.team_dropdown = self.make_labeled_dropdown(
            controls,
            "Team",
            "All teams",
            ["All teams"],
            "teams",
        )

        fetch_button = Button(text="Fetch", size_hint_x=None, width=96)
        fetch_button.bind(on_press=lambda _button: self.fetch_resource())
        controls.add_widget(fetch_button)
        controls_box.add_widget(controls)

        quick_buttons = BoxLayout(orientation="horizontal", size_hint_y=None, height=34, spacing=5)
        for label, resource in [
            ("Scoreboard", "scoreboard"),
            ("Teams", "teams"),
            ("Bills team", f"teams/{DEFAULT_TEAM_SLUG}"),
            ("News", "news"),
            ("Game summary", f"summary?event={DEFAULT_EVENT_ID}"),
        ]:
            button = Button(text=label)
            button.bind(on_press=lambda _button, value=resource: self.set_resource_path(value, True))
            quick_buttons.add_widget(button)
        controls_box.add_widget(quick_buttons)

        path_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=34, spacing=5)
        path_row.add_widget(Label(text="Path", size_hint_x=None, width=48))
        self.resource_path_input = TextInput(text="scoreboard", multiline=False, write_tab=False)
        self.resource_path_input.bind(text=lambda *_args: self.update_url_preview())
        path_row.add_widget(self.resource_path_input)
        controls_box.add_widget(path_row)

        self.url_label = Label(text="", size_hint_y=None, height=44, halign="left", valign="middle")
        self.url_label.bind(size=lambda label, _size: setattr(label, "text_size", label.size))
        controls_box.add_widget(self.url_label)

        ids.api_preview.clear_widgets()
        ids.api_preview.cols = 1
        self.output = TextInput(
            text="",
            readonly=True,
            font_size=13,
            background_color=(0.025, 0.035, 0.055, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.95, 0.97, 1.0, 1),
        )
        ids.api_preview.add_widget(self.output)

        self.debug_toggle = ids.debug_nav_button
        self.debug_output = TextInput(
            text="Debug log ready.",
            readonly=True,
            font_size=11,
            background_color=(0.018, 0.026, 0.040, 1),
            foreground_color=(0.78, 0.92, 1.0, 1),
            cursor_color=(0.78, 0.92, 1.0, 1),
        )
        self.debug_container = ids.debug_body
        self.debug_container.add_widget(self.debug_output)
        self.root_screen.debug_open = False
        self.debug_toggle.text = "Show Debug"
        self.setup_settings_panel()
        ids.favorites_list.text = self.make_favorites_summary()
        ids.favorites_main.text = self.make_favorites_summary()
        ids.upcoming_events.clear_widgets()
        ids.upcoming_events.add_widget(Label(
            text="Current game details now live in the carousel.",
            color=(0.78, 0.84, 0.92, 1),
            size_hint_y=None,
            height=42,
            halign="left",
            valign="top",
        ))
        self.set_loading_status("Ready.", False)
        if self.calendar_feature_enabled:
            self.setup_next_four_weeks_panel()
            self.build_calendar_view()

    def set_loading_status(self, text, loading=False):
        if not hasattr(self, "root_screen"):
            return

        ids = self.root_screen.ids
        if "api_status" in ids:
            ids.api_status.text = text
        if "api_loading_spinner" in ids:
            ids.api_loading_spinner.active = bool(loading)

    def setup_home_dashboard(self):
        ids = self.root_screen.ids

        self.render_today_summary()
        self.render_dashboard_sport_filters()
        self.setup_live_carousel_shell()
        self.live_game_slides = [
            CarouselMessageCard(
                title="Loading scoreboard",
                message="Live and upcoming games will appear here.",
            ),
        ]
        self.live_game_index = 0
        self.now_next_items = []
        self.now_next_index = 0
        self.render_live_carousel_slide()

        ids.headline_cards.clear_widgets()
        ids.headline_cards.cols = 1
        self.headline_articles = []
        self.headline_index = 0
        self.render_headline_empty_state("Loading headlines", "ESPN news will appear here when the feed returns articles.")

    def render_today_summary(self, live=None, today=None, upcoming=None, next_label=None):
        if not hasattr(self, "root_screen"):
            return

        if live is not None:
            self.dashboard_today_stats["live"] = live
        if today is not None:
            self.dashboard_today_stats["today"] = today
        if upcoming is not None:
            self.dashboard_today_stats["upcoming"] = upcoming
        if next_label is not None:
            self.dashboard_today_stats["next"] = next_label

        stats = self.dashboard_today_stats
        ids = self.root_screen.ids
        ids.today_summary.clear_widgets()
        for value, label, accent in [
            (str(stats["live"]), "Live", [0.48, 0.88, 0.72, 1]),
            (str(stats["today"]), "Today", [0.30, 0.62, 1.00, 1]),
            (str(stats["upcoming"]), "Upcoming", [1.00, 0.55, 0.05, 1]),
            (stats["next"], "Next start", [0.68, 0.52, 1.00, 1]),
        ]:
            ids.today_summary.add_widget(Factory.SummaryMetric(
                value=value,
                label=label,
                accent=accent,
            ))

    def render_dashboard_sport_filters(self):
        if not hasattr(self, "root_screen"):
            return

        ids = self.root_screen.ids
        if "dashboard_sport_filters" not in ids:
            return

        ids.dashboard_sport_filters.clear_widgets()

    def make_sport_toggle(self, sport_key, config, compact=False):
        row = BoxLayout(orientation="horizontal", spacing=1)
        checkbox = CheckBox(
            active=sport_key in self.home_sports,
            size_hint_x=None,
            width=20 if compact else 22,
        )
        checkbox.bind(
            active=lambda _checkbox, enabled, key=sport_key: self.set_calendar_sport_enabled(key, enabled)
        )
        row.add_widget(checkbox)
        row.add_widget(Label(
            text=config["label"],
            color=config["color"],
            bold=True,
            font_size=9 if compact else 9,
            halign="left",
            valign="middle",
        ))
        return row

    def render_headline_empty_state(self, headline, description):
        ids = self.root_screen.ids
        ids.headline_cards.clear_widgets()
        ids.headline_cards.add_widget(NewsCard(
            headline=headline,
            published="",
            description=description,
            size_hint_y=None,
            height=64,
        ))

    def render_headline_cards(self):
        if not hasattr(self, "root_screen"):
            return

        ids = self.root_screen.ids
        ids.headline_cards.clear_widgets()
        ids.headline_cards.cols = 1
        articles = self.headline_articles
        if not articles:
            self.render_headline_empty_state(
                "No headlines found",
                "The selected feed returned no articles.",
            )
            return

        max_visible = 3
        max_start = max(0, len(articles) - max_visible)
        self.headline_index = max(0, min(self.headline_index, max_start))
        visible_articles = articles[self.headline_index:self.headline_index + max_visible]
        for article_index, article in enumerate(visible_articles, start=self.headline_index):
            ids.headline_cards.add_widget(NewsCard(
                headline=article.get("headline", "No headline"),
                published=format_published(article.get("published", "")),
                description=article.get("description", ""),
                image_url=get_article_image_url(article),
                opening=article_index == 0,
                flash_alpha=0.7 if article_index == 0 else 0,
                url=get_article_url(article),
                size_hint_y=None,
                height=dp(60),
            ))

        if len(articles) > max_visible:
            start = self.headline_index + 1
            end = self.headline_index + len(visible_articles)
            ids.headline_cards.add_widget(Label(
                text=f"{start}-{end} of {len(articles)}",
                color=(0.50, 0.62, 0.78, 1),
                font_size=9,
                size_hint_y=None,
                height=dp(18),
                halign="right",
                valign="middle",
                text_size=(ids.headline_cards.width, dp(18)),
            ))

    def scroll_headline_cards(self, direction):
        if not self.headline_articles:
            return False

        max_visible = 3
        max_start = max(0, len(self.headline_articles) - max_visible)
        new_index = max(0, min(self.headline_index + direction, max_start))
        if new_index == self.headline_index:
            return False

        self.headline_index = new_index
        self.render_headline_cards()
        return True

    def build_calendar_view(self):
        if not hasattr(self, "root_screen"):
            return

        today = date.today()
        month_calendar = calendar.Calendar(firstweekday=6)
        weeks = month_calendar.monthdatescalendar(today.year, today.month)
        ids = self.root_screen.ids

        ids.calendar_month_label.text = today.strftime("%B %Y")

        ids.main_calendar_header.clear_widgets()
        for day_name in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            ids.main_calendar_header.add_widget(Factory.CalendarHeader(text=day_name))

        ids.main_calendar_grid.clear_widgets()
        ids.main_calendar_grid.cols = 7
        total_events = 0
        for week in weeks:
            for day in week:
                day_events = self.calendar_events.get(day, [])
                total_events += len(day_events)
                is_current_month = day.month == today.month
                is_today = day == today
                day_widget = CalendarDay(
                    day_text=str(day.day),
                    event_date=day.isoformat(),
                    is_today=is_today,
                    overflow_text=f"+{len(day_events) - 6}" if len(day_events) > 6 else "Today" if is_today else "",
                    bg_color=self.get_calendar_day_bg(is_current_month, is_today),
                    border_color=self.get_calendar_day_border(is_current_month, is_today),
                )
                ids.main_calendar_grid.add_widget(day_widget)

                for event in day_events[:6]:
                    day_widget.ids.dots.add_widget(CalendarDot(dot_color=event["color"]))

        enabled_labels = [CALENDAR_SPORTS[key]["label"] for key in CALENDAR_SPORTS if key in self.home_sports]
        ids.main_calendar_legend.text = f"{total_events} games | {' / '.join(enabled_labels) if enabled_labels else 'no sports enabled'}"

    def setup_next_four_weeks_panel(self):
        ids = self.root_screen.ids
        ids.sport_toggles.clear_widgets()

        self.render_dashboard_sport_filters()
        self.refresh_next_four_weeks_calendar()

    def set_calendar_sport_enabled(self, sport_key, enabled):
        already_enabled = sport_key in self.home_sports
        if already_enabled == enabled:
            return

        if enabled:
            self.home_sports.add(sport_key)
        else:
            self.home_sports.discard(sport_key)

        if hasattr(self, "root_screen"):
            self.root_screen.settings_version += 1
        self.setup_settings_panel()
        self.render_dashboard_sport_filters()
        self.save_home_sports_preference()
        self.refresh_next_four_weeks_calendar()
        if self.root_screen.active_view == "home" and self.root_screen.active_sport == "all":
            self.refresh_live_and_ongoing_from_home_sports()

    def set_dashboard_module_enabled(self, module, enabled):
        already_enabled = module in self.dashboard_modules
        if already_enabled == enabled:
            return

        if enabled:
            self.dashboard_modules.add(module)
        else:
            self.dashboard_modules.discard(module)

        if hasattr(self, "root_screen"):
            self.root_screen.settings_version += 1
        self.setup_settings_panel()
        self.save_dashboard_modules_preference()
        if self.root_screen.active_view == "home":
            self.render_live_carousel_slide()
            self.render_headline_cards()
            if self.calendar_feature_enabled and self.calendar_events:
                self.render_next_four_weeks_calendar(self.calendar_events)

    def refresh_next_four_weeks_calendar(self):
        if not hasattr(self, "root_screen"):
            return

        events_by_day = self.fetch_next_four_weeks_events()
        self.calendar_events = events_by_day
        self.calendar_events_loaded = True
        self.render_next_four_weeks_calendar(events_by_day)
        self.build_calendar_view()

    def fetch_next_four_weeks_events(self):
        start_day = date.today()
        end_day = start_day + timedelta(days=27)
        date_range = f"{start_day:%Y%m%d}-{end_day:%Y%m%d}"
        events_by_day = {}

        for sport_key, config in CALENDAR_SPORTS.items():
            if sport_key not in self.home_sports:
                continue

            if sport_key == "F1":
                for entry in self.fetch_openf1_calendar_entries(config, start_day, end_day):
                    event_time = entry.get("event_time")
                    if not event_time:
                        continue

                    event_day = event_time.date()
                    if not start_day <= event_day <= end_day:
                        continue

                    events_by_day.setdefault(event_day, []).append(entry)
                continue

            try:
                data = get_resource(
                    config["sport"],
                    config["league"],
                    f"scoreboard?dates={date_range}",
                )
            except requests.RequestException as error:
                self.log_debug(f"{sport_key} calendar request failed: {error}")
                continue

            for event in data.get("events", []):
                if sport_key == "F1":
                    entries = self.make_f1_calendar_entries(event, sport_key, config, start_day, end_day)
                else:
                    entries = [self.make_team_calendar_entry(event, sport_key, config)]

                for entry in entries:
                    event_time = entry.get("event_time")
                    if not event_time:
                        continue

                    event_day = event_time.date()
                    if not start_day <= event_day <= end_day:
                        continue

                    events_by_day.setdefault(event_day, []).append(entry)

        for day_events in events_by_day.values():
            day_events.sort(key=lambda item: item.get("event_time") or datetime.max.replace(tzinfo=timezone.utc))

        return events_by_day

    def fetch_openf1_sessions_for_years(self, years):
        sessions = []
        for year in years:
            if year in self.openf1_sessions_cache:
                sessions.extend(self.openf1_sessions_cache[year])
                continue

            try:
                year_sessions = get_openf1_sessions(year)
            except requests.RequestException as error:
                self.log_debug(f"OpenF1 sessions request failed for {year}: {error}")
                year_sessions = []

            if not isinstance(year_sessions, list):
                year_sessions = []

            self.openf1_sessions_cache[year] = year_sessions
            sessions.extend(year_sessions)

        return sessions

    def fetch_openf1_calendar_entries(self, config, start_day, end_day):
        years = sorted({start_day.year, end_day.year})
        sessions = self.fetch_openf1_sessions_for_years(years)
        entries = []
        for session in sessions:
            event_time = parse_espn_datetime(session.get("date_start"))
            if not event_time:
                continue

            event_day = event_time.date()
            if not start_day <= event_day <= end_day:
                continue

            entries.append(self.make_openf1_calendar_entry(session, config, event_time))

        return entries

    def make_openf1_calendar_entry(self, session, config, event_time=None):
        event_time = event_time or parse_espn_datetime(session.get("date_start"))
        session_name = session.get("session_name") or session.get("session_type") or "Session"
        country = session.get("country_name", "")
        circuit = session.get("circuit_short_name", "")
        location = session.get("location", "")
        meeting_key = session.get("meeting_key", "")
        session_key = session.get("session_key", "")
        event_name = f"{country} Grand Prix" if country else "Formula 1"
        venue_name = circuit or location or country

        return {
            "sport": "F1",
            "label": config["label"],
            "color": config["color"],
            "api_source": "OpenF1",
            "api_endpoint": "sessions",
            "event_id": str(session_key),
            "competition_id": str(meeting_key),
            "name": f"{event_name} - {session_name}",
            "event_name": event_name,
            "event_time": event_time,
            "time": self.format_time_only(event_time),
            "status": "Cancelled" if session.get("is_cancelled") else "Scheduled",
            "venue": {
                "fullName": venue_name,
                "address": {
                    "city": location,
                    "country": country,
                },
            },
            "session": session_name,
            "session_key": session_key,
            "meeting_key": meeting_key,
            "location": location,
            "country_code": session.get("country_code", ""),
            "country_name": country,
            "circuit_short_name": circuit,
            "raw_session": session,
        }

    def make_team_calendar_entry(self, event, sport_key, config):
        competition = event.get("competitions", [{}])[0]
        event_time = parse_espn_datetime(competition.get("date") or event.get("date"))
        venue = competition.get("venue", {}) or event.get("venue", {}) or {}
        competitors = competition.get("competitors", [])
        teams = []
        for competitor in competitors:
            team = competitor.get("team", {})
            teams.append({
                "side": competitor.get("homeAway", ""),
                "name": team.get("displayName", team.get("name", "Unknown team")),
                "abbreviation": team.get("abbreviation", ""),
                "logo": get_team_logo(team),
                "color": hex_to_rgba(team.get("color", "")),
                "score": str(competitor.get("score", "-")),
            })

        return {
            "sport": sport_key,
            "label": config["label"],
            "color": config["color"],
            "api_sport": config["sport"],
            "api_league": config["league"],
            "event_id": str(event.get("id", "")),
            "name": event.get("shortName", event.get("name", "Game")),
            "event_time": event_time,
            "time": self.format_time_only(event_time),
            "status": event.get("status", {}).get("type", {}).get("description", ""),
            "venue": venue,
            "teams": teams,
            "raw_event": event,
        }

    def make_f1_calendar_entries(self, event, sport_key, config, start_day, end_day):
        circuit = event.get("circuit", {}) or {}
        entries = []
        competitions = event.get("competitions", []) or [{}]

        for competition in competitions:
            event_time = parse_espn_datetime(
                competition.get("startDate") or competition.get("date") or event.get("date")
            )
            if not event_time:
                continue

            event_day = event_time.date()
            if not start_day <= event_day <= end_day:
                continue

            abbreviation = competition.get("type", {}).get("abbreviation", "")
            session_name = F1_SESSION_LABELS.get(abbreviation, abbreviation or "Session")
            broadcast = competition.get("broadcast", "")
            entries.append({
                "sport": sport_key,
                "label": config["label"],
                "color": config["color"],
                "api_sport": config["sport"],
                "api_league": config["league"],
                "event_id": str(event.get("id", "")),
                "competition_id": str(competition.get("id", "")),
                "name": f"{event.get('shortName', event.get('name', 'Grand Prix'))} - {session_name}",
                "event_time": event_time,
                "time": self.format_time_only(event_time),
                "status": competition.get("status", {}).get("type", {}).get("description", ""),
                "venue": circuit,
                "session": session_name,
                "broadcast": broadcast,
                "raw_event": event,
                "raw_competition": competition,
            })

        return entries

    def format_time_only(self, event_time):
        if not event_time:
            return "time unavailable"
        return event_time.strftime("%#I:%M %p") if sys.platform == "win32" else event_time.strftime("%-I:%M %p")

    def render_next_four_weeks_calendar(self, events_by_day):
        ids = self.root_screen.ids
        today = date.today()
        week_start = today - timedelta(days=(today.weekday() + 1) % 7)
        days = [week_start + timedelta(days=index) for index in range(28)]

        ids.calendar_header.clear_widgets()
        for day_name in ["S", "M", "T", "W", "T", "F", "S"]:
            ids.calendar_header.add_widget(Factory.CalendarHeader(text=day_name))

        ids.calendar_grid.clear_widgets()
        ids.calendar_grid.cols = 7
        total_events = 0
        for day in days:
            day_events = events_by_day.get(day, [])
            total_events += len(day_events)
            in_window = today <= day <= today + timedelta(days=27)
            day_widget = CalendarDay(
                day_text=str(day.day),
                event_date=day.isoformat(),
                is_today=day == today,
                overflow_text=f"+{len(day_events) - 6}" if len(day_events) > 6 else "",
                bg_color=self.get_calendar_day_bg(in_window, day == today),
                border_color=self.get_calendar_day_border(in_window, day == today),
            )
            ids.calendar_grid.add_widget(day_widget)

            for event in day_events[:6]:
                day_widget.ids.dots.add_widget(CalendarDot(dot_color=event["color"]))

        enabled_labels = [CALENDAR_SPORTS[key]["label"] for key in CALENDAR_SPORTS if key in self.home_sports]
        ids.calendar_legend.text = f"{total_events} games | {' / '.join(enabled_labels) if enabled_labels else 'no sports enabled'}"

    def open_calendar_day(self, day_iso):
        try:
            selected_day = date.fromisoformat(day_iso)
        except ValueError:
            return

        if not self.calendar_events:
            self.refresh_next_four_weeks_calendar()

        self.calendar_day_request_id += 1
        request_id = self.calendar_day_request_id
        self.open_calendar_day_popup(selected_day)
        self.show_debug_for_current_view()
        Clock.schedule_once(
            lambda _dt: self.finish_calendar_day_open(request_id, selected_day),
            0,
        )

    def finish_calendar_day_open(self, request_id, selected_day):
        if request_id != self.calendar_day_request_id:
            return

        self.render_calendar_day_detail(selected_day, self.calendar_events.get(selected_day, []))

    def open_calendar_day_popup(self, selected_day):
        if self.calendar_day_popup:
            self.calendar_day_popup.dismiss()

        self.calendar_day_popup = CalendarDayPopup(
            title_text=selected_day.strftime("%A, %B %d"),
            subtitle_text="Loading events...",
        )
        self.render_calendar_day_loading(selected_day)
        self.calendar_day_popup.open()

    def render_calendar_day_loading(self, selected_day):
        if not self.calendar_day_popup:
            return

        body = self.calendar_day_popup.ids.events_body
        body.clear_widgets()
        body.cols = 1
        loading_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(180),
            spacing=dp(10),
            padding=(0, 0),
        )
        loading_row.add_widget(Widget())
        loading_row.add_widget(LoadingSpinner(
            active=True,
            size_hint_x=None,
            width=dp(42),
        ))
        label = Label(
            text=f"Loading events for {selected_day.strftime('%A, %B %d')}...",
            color=(0.72, 0.92, 1, 1),
            bold=True,
            font_size=18,
            size_hint_x=None,
            width=dp(360),
            halign="left",
            valign="middle",
        )
        label.bind(size=lambda item, _size: setattr(item, "text_size", item.size))
        loading_row.add_widget(label)
        loading_row.add_widget(Widget())
        body.add_widget(loading_row)
        body.height = loading_row.height

    def render_calendar_day_detail(self, selected_day, events):
        if not self.calendar_day_popup:
            return

        self.calendar_day_popup.title_text = selected_day.strftime("%A, %B %d")
        self.calendar_day_popup.subtitle_text = f"{len(events)} event{'s' if len(events) != 1 else ''} found"
        body = self.calendar_day_popup.ids.events_body
        body.clear_widgets()
        body.cols = 1

        if not events:
            empty = Label(
                text="No events found for this date.\nUse the sport toggles in Next 4 Weeks to add or remove feeds.",
                color=(0.76, 0.83, 0.92, 1),
                font_size=14,
                size_hint_y=None,
                height=180,
                halign="center",
                valign="middle",
            )
            empty.bind(size=lambda label, _size: setattr(label, "text_size", label.size))
            body.add_widget(empty)
            body.height = empty.height
            return

        for event in events:
            body.add_widget(self.make_calendar_event_card(event))
        body.height = (
            len(body.children) * CALENDAR_DAY_CARD_HEIGHT
            + max(0, len(body.children) - 1) * CALENDAR_DAY_CARD_SPACING
        )

    def make_calendar_event_card(self, event):
        venue = event.get("venue", {}) or {}
        venue_name = venue.get("fullName", "Venue unavailable")
        address = venue.get("address", {})
        venue_location = ", ".join([
            value for value in [
                address.get("city", ""),
                address.get("state", ""),
                address.get("country", ""),
            ]
            if value
        ])
        teams = event.get("teams", [])
        away = next((team for team in teams if team.get("side") == "away"), {})
        home = next((team for team in teams if team.get("side") == "home"), {})

        card = CalendarDayEventCard(
            event_id=event.get("event_id", ""),
            sport=event.get("sport", ""),
            sport_label=event.get("label", event.get("sport", "SPORT")),
            title=event.get("name", "Event"),
            time_text=event.get("time", "time unavailable"),
            status_text=event.get("status") or "Scheduled",
            venue_text=f"{venue_name} - {venue_location}" if venue_location else venue_name,
            weather_icon="",
            weather_text="Loading forecast...",
            away_name=away.get("name", ""),
            away_abbreviation=away.get("abbreviation", ""),
            away_logo=away.get("logo", ""),
            away_color=away.get("color", [0.95, 0.98, 1, 1]),
            home_name=home.get("name", ""),
            home_abbreviation=home.get("abbreviation", ""),
            home_logo=home.get("logo", ""),
            home_color=home.get("color", [0.95, 0.98, 1, 1]),
            session_text=event.get("session", ""),
            broadcast_text=event.get("broadcast", ""),
            sport_color=event.get("color", [0.30, 0.62, 1, 1]),
            is_f1=event.get("sport") == "F1",
            size_hint_y=None,
            height=CALENDAR_DAY_CARD_HEIGHT,
        )
        self.load_calendar_card_weather(card, venue, event.get("event_time"), event.get("label", ""))
        return card

    def load_calendar_card_weather(self, card, venue, event_time, fallback_label):
        address = venue.get("address", {}) if isinstance(venue, dict) else {}
        if not address.get("city"):
            card.weather_text = "Weather unavailable"
            return

        def worker():
            weather = self.get_projected_weather_for_venue(venue, event_time, fallback_label)
            Clock.schedule_once(lambda _dt: self.apply_calendar_card_weather(card, weather), 0)

        threading.Thread(target=worker, daemon=True).start()

    def apply_calendar_card_weather(self, card, weather):
        card.weather_icon = weather.get("icon", "")
        card.weather_text = weather.get("text", "Weather unavailable")

    def make_calendar_day_detail_text(self, selected_day, events):
        if not events:
            return "\n".join([
                "No events found for this date.",
                "",
                "Use the sport toggles in Next 4 Weeks to add or remove feeds.",
            ])

        lines = [
            f"{len(events)} event{'s' if len(events) != 1 else ''} found",
            "",
        ]

        for index, event in enumerate(events, start=1):
            venue = event.get("venue", {}) or {}
            venue_name = venue.get("fullName", "Venue unavailable")
            address = venue.get("address", {})
            venue_location = ", ".join([
                value for value in [
                    address.get("city", ""),
                    address.get("state", ""),
                    address.get("country", ""),
                ]
                if value
            ])
            weather = self.get_projected_weather_for_venue(venue, event.get("event_time"), event.get("label", ""))

            lines.extend([
                f"{index}. [{event.get('label', event.get('sport', 'SPORT'))}] {event.get('name', 'Event')}",
                f"Time: {event.get('time', 'time unavailable')}",
                f"Status: {event.get('status') or 'Scheduled'}",
                f"Where: {venue_name}",
                f"Location: {venue_location or 'Location unavailable'}",
                f"Projected weather: {weather.get('text', 'Weather unavailable')}",
            ])

            teams = event.get("teams", [])
            if teams:
                away = next((team for team in teams if team.get("side") == "away"), {})
                home = next((team for team in teams if team.get("side") == "home"), {})
                if away or home:
                    lines.append(
                        "Who's playing: "
                        f"{away.get('name', 'Away team')} ({away.get('abbreviation', '-')}) "
                        "at "
                        f"{home.get('name', 'Home team')} ({home.get('abbreviation', '-')})"
                    )
                else:
                    lines.append("Who's playing: " + " vs ".join(team.get("name", "Unknown team") for team in teams))

            if event.get("sport") == "F1":
                lines.append(f"Session: {event.get('session', 'F1 session')}")
                lines.append("Who's competing: Formula 1 field")
                if event.get("broadcast"):
                    lines.append(f"Broadcast: {event['broadcast']}")

            if event.get("event_id") and event.get("sport") != "F1":
                lines.append(f"Game ID: {event['event_id']} (click the live game card for full game summary when available)")

            lines.append("")

        return "\n".join(lines).strip()

    def get_calendar_day_bg(self, is_current_month, is_today):
        if is_today:
            return [0.10, 0.28, 0.80, 1]
        if is_current_month:
            return [0.035, 0.060, 0.105, 1]
        return [0.020, 0.032, 0.052, 1]

    def get_calendar_day_border(self, is_current_month, is_today):
        if is_today:
            return [0.48, 0.88, 0.72, 1]
        if is_current_month:
            return [0.08, 0.12, 0.18, 1]
        return [0.04, 0.06, 0.09, 1]

    def setup_live_carousel_shell(self):
        ids = self.root_screen.ids
        ids.live_games.clear_widgets()
        ids.live_games.cols = 1
        self.live_carousel_body = ids.live_games
        if not getattr(self, "live_carousel_size_bound", False):
            ids.live_games.bind(size=lambda *_args: Clock.schedule_once(lambda _dt: self.render_now_next_cards(), 0))
            self.live_carousel_size_bound = True

    def make_end_slide(self):
        return CarouselMessageCard(
            title="End of list",
            message="No additional games are queued for this view.",
        )

    def show_previous_live_slide(self):
        self.scroll_now_next_cards(-1)

    def show_next_live_slide(self):
        self.scroll_now_next_cards(1)

    def render_live_carousel_slide(self):
        if not hasattr(self, "live_carousel_body"):
            return

        self.live_carousel_body.clear_widgets()
        if not self.live_game_slides:
            self.now_next_items = []
            self.now_next_index = 0
            self.render_now_next_cards()
            return

        visible_items = [
            item
            for item in self.live_game_slides
            if not (isinstance(item, CarouselMessageCard) and item.title == "End of list")
        ]
        if not visible_items:
            visible_items = [CarouselMessageCard(
                title="No games found",
                message="Try enabling another sport or refreshing the dashboard.",
            )]

        self.now_next_items = visible_items
        page_size = self.get_now_next_page_size()
        self.now_next_index = max(0, min(self.now_next_index, max(0, len(self.now_next_items) - page_size)))
        self.render_now_next_cards()

    def get_now_next_page_size(self):
        available_height = self.get_now_next_available_height()
        if available_height <= 0:
            return 3

        if available_height >= dp(350):
            return 3
        if available_height >= dp(235):
            return 2
        return 1

    def get_now_next_available_height(self):
        available_height = 0
        if hasattr(self, "live_carousel_body"):
            available_height = max(available_height, self.live_carousel_body.height)
        if hasattr(self, "root_screen"):
            now_next_zone = self.root_screen.ids.get("now_next_zone")
            if now_next_zone:
                available_height = max(available_height, now_next_zone.height - dp(31))
        return available_height

    def get_now_next_card_height(self, page_size, has_footer):
        available_height = self.get_now_next_available_height()
        if available_height <= 0:
            return dp(136)

        footer_height = dp(20) if has_footer else 0
        spacing_count = max(0, page_size - 1) + (1 if has_footer else 0)
        spacing_height = dp(4) * spacing_count
        card_height = (available_height - footer_height - spacing_height) / max(1, page_size)
        return max(dp(112), min(dp(150), card_height))

    def render_now_next_cards(self):
        if not hasattr(self, "live_carousel_body"):
            return

        self.live_carousel_body.clear_widgets()
        if not self.now_next_items:
            self.live_carousel_body.add_widget(CarouselMessageCard(
                title="No games found",
                message="Try enabling another sport or refreshing the dashboard.",
                size_hint_y=None,
                height=dp(96),
            ))
            return

        max_visible_now_next = self.get_now_next_page_size()
        max_start = max(0, len(self.now_next_items) - max_visible_now_next)
        self.now_next_index = max(0, min(self.now_next_index, max_start))
        visible_items = self.now_next_items[self.now_next_index:self.now_next_index + max_visible_now_next]
        has_footer = len(self.now_next_items) > max_visible_now_next
        card_height = self.get_now_next_card_height(len(visible_items), has_footer)
        for item in visible_items:
            item.size_hint_y = None
            item.height = card_height if isinstance(item, (SmallEventCard, F1SessionCard)) else min(dp(96), card_height)
            self.live_carousel_body.add_widget(item)

        if has_footer:
            start = self.now_next_index + 1
            end = self.now_next_index + len(visible_items)
            self.live_carousel_body.add_widget(Label(
                text=f"{start}-{end} of {len(self.now_next_items)}",
                color=(0.50, 0.62, 0.78, 1),
                font_size=9,
                size_hint_y=None,
                height=dp(20),
                halign="right",
                valign="middle",
                text_size=(self.live_carousel_body.width, dp(20)),
            ))

    def scroll_now_next_cards(self, direction):
        if not self.now_next_items:
            return False

        max_visible = self.get_now_next_page_size()
        max_start = max(0, len(self.now_next_items) - max_visible)
        new_index = max(0, min(self.now_next_index + direction, max_start))
        if new_index == self.now_next_index:
            return False

        self.now_next_index = new_index
        self.render_now_next_cards()
        return True

    def open_event_card_overlay(self, card, suppress_drag_guard=False):
        if not suppress_drag_guard and time.monotonic() - getattr(self, "last_dashboard_drag_at", 0) < 0.25:
            return

        self.show_busy_overlay("Retrieving data...")
        Clock.schedule_once(lambda _dt, selected_card=card: self._open_event_card_overlay(selected_card), 0.05)

    def _open_event_card_overlay(self, card):
        payload = getattr(card, "detail_payload", None)
        if isinstance(payload, dict) and payload.get("api_source") == "OpenF1":
            self.open_f1_session_overlay(card, payload)
            return

        if isinstance(card, SmallEventCard):
            self.open_standard_game_overlay(card)
            return

        if self.event_detail_popup is not None:
            self.event_detail_popup.dismiss()
            self.event_detail_popup = None

        content = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )
        details = [
            ("Title", getattr(card, "title", "Upcoming event") or "Upcoming event"),
            ("Date", getattr(card, "date_text", "") or getattr(card, "time_text", "") or "Time unavailable"),
            ("Status / Time", getattr(card, "time_text", "") or "Status unavailable"),
            ("Location", getattr(card, "venue_text", "") or "Location unavailable"),
        ]

        message = getattr(card, "message", "")
        if message:
            details.append(("Info", message))

        teams = self.format_event_card_teams(card)
        if teams:
            details.append(("Teams", teams))

        weather = getattr(card, "weather_text", "")
        if weather:
            details.append(("Weather", weather))

        event_id = getattr(card, "event_id", "")
        if event_id:
            details.append(("Event ID", event_id))

        header = Label(
            text="[b]Event Details[/b]",
            markup=True,
            color=(0.96, 0.98, 1, 1),
            font_size="20sp",
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            text_size=(dp(520), dp(30)),
        )
        content.add_widget(header)

        for label, value in details:
            content.add_widget(Label(
                text=f"[b]{label}[/b]\n{value}",
                markup=True,
                color=(0.82, 0.88, 0.96, 1),
                font_size="14sp",
                size_hint_y=None,
                height=dp(54),
                halign="left",
                valign="top",
                text_size=(dp(520), dp(54)),
            ))

        content.add_widget(Widget())
        close_button = Button(
            text="Close",
            size_hint_y=None,
            height=dp(42),
            background_normal="",
            background_color=(0.12, 0.25, 0.52, 1),
            color=(0.96, 0.98, 1, 1),
        )
        content.add_widget(close_button)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.68, 0.70),
            auto_dismiss=True,
            background_color=(0.018, 0.026, 0.040, 0.98),
            separator_height=0,
        )
        close_button.bind(on_release=popup.dismiss)
        popup.bind(on_dismiss=lambda *_args: setattr(self, "event_detail_popup", None))
        self.event_detail_popup = popup
        self.hide_busy_overlay()
        popup.open()

    def open_standard_game_overlay(self, card):
        if self.event_detail_popup is not None:
            self.event_detail_popup.dismiss()
            self.event_detail_popup = None

        summary = self.fetch_game_summary(
            getattr(card, "event_id", ""),
            getattr(card, "sport_slug", "") or None,
            getattr(card, "league_slug", "") or None,
        )
        matchup = self.make_matchup_overlay_data(card, summary)
        content = self.build_matchup_overlay_content(matchup)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.78, 0.82),
            auto_dismiss=True,
            background_color=(0.018, 0.026, 0.040, 0.98),
            separator_height=0,
        )
        popup.bind(on_dismiss=lambda *_args: setattr(self, "event_detail_popup", None))
        self.event_detail_popup = popup
        self.hide_busy_overlay()
        popup.open()

    def make_matchup_overlay_data(self, card, summary):
        competition = {}
        header = {}
        if isinstance(summary, dict):
            header = summary.get("header", {}) or {}
            competitions = header.get("competitions", [])
            competition = competitions[0] if competitions else {}

        status = competition.get("status", {}) or {}
        status_text = format_game_clock(status, competition.get("date")) if status else getattr(card, "time_text", "")
        venue = competition.get("venue", {}) or {}
        venue_text = self.format_venue_text(venue) or getattr(card, "venue_text", "")
        broadcasts = self.format_broadcasts(competition)

        away = self.get_overlay_team(competition, "away", card)
        home = self.get_overlay_team(competition, "home", card)
        details = [
            ("Status", status_text or "Status unavailable"),
            ("Start", format_event_datetime(competition.get("date")) or getattr(card, "date_text", "") or "Time unavailable"),
            ("Venue", venue_text or "Location unavailable"),
            ("Weather", getattr(card, "weather_text", "") or "Weather unavailable"),
        ]
        if broadcasts:
            details.append(("Broadcast", broadcasts))

        return {
            "title": header.get("name") or getattr(card, "title", "Game detail"),
            "league": (getattr(card, "league_slug", "") or "").upper(),
            "status": status_text or getattr(card, "time_text", ""),
            "away": away,
            "home": home,
            "details": details,
            "leaders": self.extract_overlay_leaders(summary),
            "plays": self.extract_overlay_plays(summary),
            "event_id": getattr(card, "event_id", ""),
            "summary_loaded": isinstance(summary, dict),
        }

    def get_overlay_team(self, competition, side, card):
        competitors = competition.get("competitors", []) if isinstance(competition, dict) else []
        for competitor in competitors:
            if competitor.get("homeAway") != side:
                continue
            team = competitor.get("team", {}) or {}
            records = [
                item.get("summary", "")
                for item in competitor.get("records", [])
                if item.get("summary")
            ]
            return {
                "name": team.get("displayName") or team.get("shortDisplayName") or team.get("name") or side.title(),
                "abbreviation": team.get("abbreviation") or "?",
                "logo": get_team_logo(team),
                "score": str(competitor.get("score", "-")),
                "color": hex_to_rgba(team.get("color", "")),
                "record": " / ".join(records[:2]),
            }

        prefix = "away" if side == "away" else "home"
        return {
            "name": getattr(card, f"{prefix}_abbreviation", side.title()),
            "abbreviation": getattr(card, f"{prefix}_abbreviation", "?"),
            "logo": getattr(card, f"{prefix}_logo", ""),
            "score": getattr(card, f"{prefix}_score", "-"),
            "color": getattr(card, f"{prefix}_color", [0.95, 0.98, 1, 1]),
            "record": "",
        }

    def build_matchup_overlay_content(self, matchup):
        content = BoxLayout(orientation="vertical", padding=dp(18), spacing=dp(12))
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(34), spacing=dp(8))
        header.add_widget(Label(
            text=f"[b]{matchup['league'] or 'GAME'}[/b]  {matchup['status'] or 'Details'}",
            markup=True,
            color=(0.52, 0.82, 1, 1),
            font_size="13sp",
            halign="left",
            valign="middle",
            text_size=(dp(420), dp(34)),
        ))
        close_button = Button(
            text="Close",
            size_hint_x=None,
            width=dp(86),
            background_normal="",
            background_color=(0.12, 0.25, 0.52, 1),
            color=(0.96, 0.98, 1, 1),
        )
        header.add_widget(close_button)
        content.add_widget(header)

        score_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(104), spacing=dp(10))
        score_row.add_widget(self.make_overlay_team_panel(matchup["away"], "right"))
        score_row.add_widget(Label(
            text="@",
            color=(0.48, 0.58, 0.70, 1),
            bold=True,
            font_size="18sp",
            size_hint_x=None,
            width=dp(28),
            halign="center",
            valign="middle",
            text_size=(dp(28), dp(104)),
        ))
        score_row.add_widget(self.make_overlay_team_panel(matchup["home"], "left"))
        content.add_widget(score_row)

        content.add_widget(self.make_overlay_details_grid(matchup["details"]))

        scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=dp(6))
        body = GridLayout(cols=1, spacing=dp(8), size_hint_y=None)
        body.bind(minimum_height=body.setter("height"))
        body.add_widget(self.make_overlay_section("Recent Plays", matchup["plays"] or ["No recent play data available."]))
        body.add_widget(self.make_overlay_section("Leaders", matchup["leaders"] or ["Leader data unavailable."]))
        if not matchup["summary_loaded"]:
            body.add_widget(self.make_overlay_section("Summary", ["Detailed ESPN summary was unavailable; showing card data."]))
        scroll.add_widget(body)
        content.add_widget(scroll)

        close_button.bind(on_release=lambda *_args: self.event_detail_popup.dismiss() if self.event_detail_popup else None)
        return content

    def make_overlay_team_panel(self, team, align):
        panel = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(4))
        panel.canvas.before.clear()
        with panel.canvas.before:
            Color(0.035, 0.055, 0.090, 1)
            Rectangle(pos=panel.pos, size=panel.size)
        panel.bind(pos=lambda widget, *_args: self.redraw_plain_panel(widget), size=lambda widget, *_args: self.redraw_plain_panel(widget))
        top = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(30))
        if align == "right":
            top.add_widget(Label(
                text=team.get("abbreviation", "?"),
                color=team.get("color", [0.95, 0.98, 1, 1]),
                bold=True,
                font_size="20sp",
                halign="right",
                valign="middle",
                text_size=(dp(160), dp(30)),
            ))
        top.add_widget(AsyncImage(
            source=team.get("logo", ""),
            fit_mode="contain",
            size_hint_x=None,
            width=dp(30),
        ))
        if align != "right":
            top.add_widget(Label(
                text=team.get("abbreviation", "?"),
                color=team.get("color", [0.95, 0.98, 1, 1]),
                bold=True,
                font_size="20sp",
                halign="left",
                valign="middle",
                text_size=(dp(160), dp(30)),
            ))
        panel.add_widget(top)
        panel.add_widget(Label(
            text=team.get("name", ""),
            color=(0.68, 0.76, 0.88, 1),
            font_size="10sp",
            shorten=True,
            shorten_from="right",
            halign=align,
            valign="middle",
            text_size=(dp(210), dp(16)),
            size_hint_y=None,
            height=dp(16),
        ))
        panel.add_widget(Label(
            text=team.get("score", "-"),
            color=(0.98, 0.99, 1, 1),
            bold=True,
            font_size="28sp",
            halign=align,
            valign="middle",
            text_size=(dp(210), dp(34)),
            size_hint_y=None,
            height=dp(34),
        ))
        panel.add_widget(Label(
            text=team.get("record") or team.get("name", ""),
            color=(0.68, 0.76, 0.88, 1),
            font_size="11sp",
            shorten=True,
            shorten_from="right",
            halign=align,
            valign="middle",
            text_size=(dp(210), dp(20)),
        ))
        return panel

    def redraw_plain_panel(self, widget):
        widget.canvas.before.clear()
        with widget.canvas.before:
            Color(0.035, 0.055, 0.090, 1)
            Rectangle(pos=widget.pos, size=widget.size)

    def make_overlay_details_grid(self, details):
        grid = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(96))
        for label, value in details[:6]:
            grid.add_widget(Label(
                text=f"[b]{label}[/b]\n{value}",
                markup=True,
                color=(0.78, 0.86, 0.96, 1),
                font_size="11sp",
                halign="left",
                valign="top",
                text_size=(dp(260), dp(42)),
            ))
        return grid

    def make_overlay_section(self, title, lines):
        section = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        height = dp(28 + max(1, len(lines)) * 22)
        section.height = height
        section.add_widget(Label(
            text=f"[b]{title}[/b]",
            markup=True,
            color=(0.96, 0.98, 1, 1),
            font_size="14sp",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            text_size=(dp(560), dp(24)),
        ))
        for line in lines[:6]:
            section.add_widget(Label(
                text=line,
                color=(0.72, 0.80, 0.92, 1),
                font_size="11sp",
                size_hint_y=None,
                height=dp(20),
                shorten=True,
                shorten_from="right",
                halign="left",
                valign="middle",
                text_size=(dp(560), dp(20)),
            ))
        return section

    def format_venue_text(self, venue):
        if not isinstance(venue, dict):
            return ""
        address = venue.get("address", {}) or {}
        location = ", ".join(part for part in [address.get("city", ""), address.get("state") or address.get("country", "")] if part)
        if venue.get("fullName") and location:
            return f"{venue['fullName']} - {location}"
        return venue.get("fullName", "") or location

    def format_broadcasts(self, competition):
        names = []
        broadcasts = competition.get("broadcasts", []) if isinstance(competition, dict) else []
        for broadcast in broadcasts:
            media = broadcast.get("media", {}) or {}
            name = media.get("shortName") or media.get("name")
            if name:
                names.append(name)
        return ", ".join(names[:3])

    def extract_overlay_plays(self, summary):
        if not isinstance(summary, dict):
            return []
        plays = summary.get("plays") or summary.get("scoringPlays") or []
        lines = []
        for play in list(plays)[-5:]:
            text = play.get("text") or play.get("shortText") or play.get("displayText")
            clock = (play.get("clock") or {}).get("displayValue", "")
            period = (play.get("period") or {}).get("displayValue", "")
            prefix = " ".join(part for part in [period, clock] if part)
            if text:
                lines.append(f"{prefix}: {text}" if prefix else text)
        return lines[::-1]

    def extract_overlay_leaders(self, summary):
        if not isinstance(summary, dict):
            return []
        lines = []
        for group in summary.get("leaders", [])[:4]:
            group_name = group.get("displayName") or group.get("name") or "Leader"
            for leader in group.get("leaders", [])[:2]:
                athlete = leader.get("athlete", {}) or {}
                name = athlete.get("shortName") or athlete.get("displayName") or "Unknown"
                value = leader.get("displayValue") or str(leader.get("value", ""))
                lines.append(f"{group_name}: {name} - {value}")
        return lines

    def show_busy_overlay(self, text="Retrieving data..."):
        if hasattr(self, "root_screen"):
            self.root_screen.busy = True
            self.root_screen.busy_text = text

        if self.busy_popup is not None:
            return

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
        content.add_widget(LoadingSpinner(active=True, size_hint_y=None, height=dp(34)))
        content.add_widget(Label(
            text=text,
            color=(0.96, 0.98, 1, 1),
            bold=True,
            font_size="15sp",
            halign="center",
            valign="middle",
            text_size=(dp(300), dp(32)),
        ))
        popup = Popup(
            title="",
            content=content,
            size_hint=(0.34, 0.18),
            auto_dismiss=False,
            background_color=(0.04, 0.07, 0.13, 0.98),
            separator_height=0,
        )
        if hasattr(popup, "overlay_color"):
            popup.overlay_color = (0.01, 0.015, 0.026, 0.72)
        self.busy_popup = popup
        popup.open()

    def hide_busy_overlay(self):
        if hasattr(self, "root_screen"):
            self.root_screen.busy = False

        popup = self.busy_popup
        self.busy_popup = None
        if popup is not None:
            popup.dismiss()

    def format_event_card_teams(self, card):
        away = getattr(card, "away_abbreviation", "")
        home = getattr(card, "home_abbreviation", "")
        away_score = getattr(card, "away_score", "")
        home_score = getattr(card, "home_score", "")
        if not away and not home:
            return ""

        away_label = away or "Away"
        home_label = home or "Home"
        if away_score not in ("", "-") or home_score not in ("", "-"):
            return f"{away_label} {away_score} at {home_label} {home_score}"
        return f"{away_label} at {home_label}"

    def open_f1_session_overlay(self, card, entry):
        if self.event_detail_popup is not None:
            self.event_detail_popup.dismiss()
            self.event_detail_popup = None

        screen = F1RaceDetailScreen()
        screen.load_latest_completed_race()

        popup = Popup(
            title="",
            content=screen,
            size_hint=(0.92, 0.88),
            auto_dismiss=True,
            background_color=(0.018, 0.026, 0.040, 0.98),
            separator_height=0,
        )
        popup.bind(on_dismiss=lambda *_args: setattr(self, "event_detail_popup", None))
        self.event_detail_popup = popup
        self.hide_busy_overlay()
        popup.open()

    def make_labeled_dropdown(self, parent, label_text, default_text, values, favorite_key):
        group = BoxLayout(orientation="vertical", spacing=4)
        group.add_widget(Label(text=label_text, size_hint_y=None, height=24))

        dropdown = FavoriteDropdown(
            text=default_text,
            values=self.sort_values(values, favorite_key),
            favorite_key=favorite_key,
            app_ref=self,
            on_select=lambda: self.on_dropdown_changed(favorite_key),
        )

        group.add_widget(dropdown)
        parent.add_widget(group)

        return dropdown

    def sort_values(self, values, favorite_key):
        return sort_with_favorites(list(values), self.favorites.get(favorite_key, []))

    def update_dropdown_values(self, dropdown, values, favorite_key):
        dropdown.set_values(self.sort_values(values, favorite_key))

    def is_favorite(self, favorite_key, value):
        return value in self.favorites.get(favorite_key, [])

    def toggle_favorite_value(self, favorite_key, selected_value):
        if selected_value.startswith("Loading"):
            return

        favorite_values = self.favorites.setdefault(favorite_key, [])

        if selected_value in favorite_values:
            favorite_values.remove(selected_value)
            action = "Removed favorite"
        else:
            favorite_values.append(selected_value)
            action = "Added favorite"

        save_favorites(self.favorites)
        if hasattr(self, "root_screen"):
            self.root_screen.ids.favorites_list.text = self.make_favorites_summary()
            self.root_screen.ids.favorites_main.text = self.make_favorites_summary()
        self.log_debug(f"{action}: {favorite_key} -> {selected_value}")

    def make_favorites_summary(self):
        lines = []
        for key, values in self.favorites.items():
            if values:
                lines.append(f"{key}: {', '.join(values[:4])}")

        if not lines:
            return "No favorites saved yet."

        return "\n".join(lines[:5])

    def apply_sport_preset(self, sport_key):
        if sport_key != "all" and not self.unfinished_features_enabled:
            return

        sport, league = SPORT_PRESETS.get(sport_key, (DEFAULT_SPORT, DEFAULT_LEAGUE))
        if sport_key == "all":
            sport, league = DEFAULT_SPORT, DEFAULT_LEAGUE

        if hasattr(self, "sport_dropdown"):
            self.sport_dropdown.set_text(sport)
        if hasattr(self, "league_dropdown"):
            self.league_dropdown.set_text(league)

        self.sync_path_from_controls()
        self.update_url_preview()
        self.log_debug(f"Dashboard sport selected: {sport_key} -> {sport}/{league}")
        if self.unfinished_features_enabled and sport_key in ("football", "basketball", "baseball", "hockey", "all"):
            self.load_teams()
        if hasattr(self, "root_screen") and self.root_screen.active_view == "home":
            self.refresh_dashboard()

    def refresh_dashboard(self):
        self.log_debug("Refreshing dashboard overview.")
        sport = self.get_selected_sport()
        league = self.get_selected_league()
        self.dashboard_debug_payloads = {}

        if getattr(self.root_screen, "active_sport", "all") == "all":
            self.refresh_live_and_ongoing_from_home_sports()
            primary_config = self.get_primary_home_sport_config()
            if primary_config:
                news = self.fetch_dashboard_payload(
                    primary_config["sport"],
                    primary_config["league"],
                    "news",
                    "News",
                )
                if isinstance(news, dict) and not news.get("articles"):
                    fallback_news = self.fetch_dashboard_payload(
                        DEFAULT_SPORT,
                        DEFAULT_LEAGUE,
                        "news",
                        "News fallback",
                    )
                    if fallback_news is not None:
                        news = fallback_news
                if news is not None:
                    self.update_dashboard_summary("news", news)
            self.show_debug_for_current_view()
            return

        scoreboard = self.fetch_dashboard_payload(sport, league, "scoreboard", "Scoreboard")
        if scoreboard is not None:
            self.update_dashboard_summary("scoreboard", scoreboard)

        news = self.fetch_dashboard_payload(sport, league, "news", "News")
        if news is not None:
            self.update_dashboard_summary("news", news)

        event_id = self.get_current_event_id(scoreboard)
        if event_id:
            summary_path = f"summary?event={event_id}"
            summary = self.fetch_dashboard_payload(sport, league, summary_path, "Current game summary")
            if summary is not None:
                self.game_summary_cache[event_id] = summary
                self.update_current_game_card(summary)

        self.show_debug_for_current_view()

    def get_primary_home_sport_config(self):
        for sport_key in CALENDAR_SPORTS:
            if sport_key in self.home_sports:
                return CALENDAR_SPORTS[sport_key]
        return None

    def refresh_live_and_ongoing_from_home_sports(self):
        if not hasattr(self, "root_screen"):
            return

        slides = []
        now = datetime.now().astimezone()
        live_count = 0
        upcoming_count = 0
        feed_errors = []
        enabled_labels = [
            CALENDAR_SPORTS[key]["label"]
            for key in CALENDAR_SPORTS
            if key in self.home_sports
        ]

        for sport_key, config in CALENDAR_SPORTS.items():
            if sport_key not in self.home_sports:
                continue

            if sport_key == "F1":
                f1_slides, f1_live, f1_upcoming = self.make_openf1_now_next_slides(config, now)
                slides.extend(f1_slides)
                live_count += f1_live
                upcoming_count += f1_upcoming
                continue

            scoreboard = self.fetch_dashboard_payload(
                config["sport"],
                config["league"],
                "scoreboard",
                f"{sport_key} scoreboard",
            )
            if not isinstance(scoreboard, dict):
                feed_errors.append(config["label"])
                continue

            for event in scoreboard.get("events", []):
                if not is_live_or_upcoming_event(event, now):
                    continue

                state = event.get("status", {}).get("type", {}).get("state", "")
                if state == "in":
                    live_count += 1
                elif state == "pre":
                    upcoming_count += 1

                slides.append(SmallEventCard(**self.parse_game_from_scoreboard_event(event, config)))

        if not slides:
            upcoming_slides = self.make_upcoming_calendar_slides(now)
            slides.extend(upcoming_slides)

        if not slides:
            selected_text = " / ".join(enabled_labels) if enabled_labels else "no enabled sports"
            slides.append(CarouselMessageCard(
                title="No events found",
                message=f"Checked {selected_text}. Toggle another sport above the calendar to include it here.",
            ))

        visible_slide_count = len(slides)
        slides.append(self.make_end_slide())
        self.live_game_slides = slides
        self.live_game_index = 0
        self.now_next_index = 0
        self.render_live_carousel_slide()

        calendar_stats = self.get_calendar_dashboard_stats(now)
        self.render_today_summary(
            live=live_count,
            today=calendar_stats["today"],
            upcoming=calendar_stats["upcoming"],
            next_label=calendar_stats["next"],
        )

        selected_text = " / ".join(enabled_labels) if enabled_labels else "No sports selected"
        calendar_upcoming = 0 if (
            slides
            and isinstance(slides[0], CarouselMessageCard)
            and slides[0].title == "No events found"
        ) else visible_slide_count
        if live_count or upcoming_count:
            self.root_screen.ids.focus_label.text = f"{selected_text} - {live_count} live, {upcoming_count} next 24h"
        elif feed_errors:
            self.root_screen.ids.focus_label.text = f"{selected_text} - feeds failed: {', '.join(feed_errors[:3])}"
        else:
            self.root_screen.ids.focus_label.text = f"{selected_text} - {calendar_upcoming} upcoming"

    def get_calendar_dashboard_stats(self, now):
        if not self.calendar_events_loaded and self.calendar_feature_enabled:
            self.refresh_next_four_weeks_calendar()

        today_count = 0
        upcoming_count = 0
        next_time = None
        today = now.date()

        for day, entries in self.calendar_events.items():
            for entry in entries:
                event_time = entry.get("event_time")
                if not event_time:
                    continue
                if day == today:
                    today_count += 1
                if event_time >= now:
                    upcoming_count += 1
                    if next_time is None or event_time < next_time:
                        next_time = event_time

        return {
            "today": today_count,
            "upcoming": upcoming_count,
            "next": self.format_next_start_label(next_time, now),
        }

    def format_next_start_label(self, event_time, now):
        if not event_time:
            return "--"
        if event_time.date() == now.date():
            return self.format_time_only(event_time)
        if event_time.date() == now.date() + timedelta(days=1):
            return "Tomorrow"
        return event_time.strftime("%b %d")

    def make_openf1_now_next_slides(self, config, now, limit=4):
        start_day = now.date()
        end_day = start_day + timedelta(days=27)
        entries = self.fetch_openf1_calendar_entries(config, start_day, end_day)
        live_count = 0
        upcoming_count = 0
        slides = []

        active_entries = []
        for entry in entries:
            event_time = entry.get("event_time")
            raw_session = entry.get("raw_session", {})
            end_time = parse_espn_datetime(raw_session.get("date_end"))
            if event_time and end_time and event_time <= now <= end_time:
                live_count += 1
                active_entries.append((event_time, entry, "Live now"))
            elif event_time and event_time >= now:
                upcoming_count += 1
                active_entries.append((event_time, entry, "Upcoming"))

        active_entries.sort(key=lambda item: item[0] or datetime.max.replace(tzinfo=timezone.utc))
        slides = [self.make_openf1_session_slide(entry, label) for _event_time, entry, label in active_entries]
        return slides[:limit], live_count, upcoming_count

    def make_openf1_session_slide(self, entry, status_label=None):
        event_time = entry.get("event_time")
        session = entry.get("session", "Session")
        status = status_label or entry.get("status", "Scheduled")
        raw_session = entry.get("raw_session", {})
        end_time = parse_espn_datetime(raw_session.get("date_end"))
        time_text = self.format_time_only(event_time) if event_time else "Time TBA"
        if end_time:
            time_text = f"{time_text}-{self.format_time_only(end_time)}"

        return F1SessionCard(
            event_id=str(entry.get("session_key", "")),
            status_label=status.upper(),
            grand_prix=entry.get("event_name") or entry.get("name", "Formula 1").split(" - ")[0],
            session_name=session,
            session_code=self.get_f1_session_code(session),
            time_text=time_text,
            circuit_text=entry.get("circuit_short_name") or "Circuit TBA",
            location_text=self.format_f1_location(entry),
            timeline_text=self.make_f1_weekend_timeline(entry, session),
            accent=[0.16, 0.92, 0.48, 1] if status == "Live now" else [1.00, 0.18, 0.22, 1],
            detail_payload=entry,
        )

    def get_f1_session_code(self, session):
        normalized = (session or "").lower()
        if "practice 1" in normalized:
            return "FP1"
        if "practice 2" in normalized:
            return "FP2"
        if "practice 3" in normalized:
            return "FP3"
        if "sprint shootout" in normalized or "sprint qualifying" in normalized:
            return "SQ"
        if "sprint" in normalized:
            return "SPR"
        if "qualifying" in normalized:
            return "Q"
        if "race" in normalized:
            return "RACE"
        return "F1"

    def format_f1_location(self, entry):
        parts = [
            entry.get("location", ""),
            entry.get("country_code") or entry.get("country_name", ""),
        ]
        return " / ".join(part for part in parts if part) or "Formula 1 field"

    def make_f1_weekend_timeline(self, entry, current_session):
        meeting_key = entry.get("meeting_key")
        raw_current = entry.get("raw_session", {})
        sessions = []
        if meeting_key:
            for candidate in self.openf1_sessions_cache.get(raw_current.get("year"), []):
                if candidate.get("meeting_key") == meeting_key and not candidate.get("is_cancelled"):
                    sessions.append(candidate)

        if not sessions:
            sessions = [raw_current] if raw_current else []

        sessions.sort(key=lambda item: item.get("date_start") or "")
        labels = []
        current_key = raw_current.get("session_key")
        for session in sessions:
            code = self.get_f1_session_code(session.get("session_name") or session.get("session_type"))
            if session.get("session_key") == current_key or session.get("session_name") == current_session:
                labels.append(f"[b]{code}[/b]")
            else:
                labels.append(code)

        return "  ".join(labels[:6]) or self.get_f1_session_code(current_session)

    def make_upcoming_calendar_slides(self, now, limit=6):
        if not self.calendar_feature_enabled:
            return []

        if not self.calendar_events:
            self.refresh_next_four_weeks_calendar()

        entries = []
        for day in sorted(self.calendar_events):
            for entry in self.calendar_events.get(day, []):
                event_time = entry.get("event_time")
                if event_time and event_time >= now:
                    entries.append(entry)

        entries.sort(key=lambda item: item.get("event_time") or datetime.max.replace(tzinfo=timezone.utc))
        slides = []
        for entry in entries[:limit]:
            if entry.get("sport") == "F1":
                if entry.get("api_source") == "OpenF1":
                    slides.append(self.make_openf1_session_slide(entry, "Upcoming"))
                else:
                    slides.append(self.make_f1_calendar_slide(entry))
                continue

            raw_event = entry.get("raw_event")
            if isinstance(raw_event, dict):
                slides.append(SmallEventCard(**self.parse_game_from_scoreboard_event(raw_event, CALENDAR_SPORTS.get(entry.get("sport")))))
            else:
                slides.append(CarouselMessageCard(
                    title=f"{entry.get('label', entry.get('sport', 'SPORT'))} - {entry.get('name', 'Upcoming event')}",
                    message=f"Starts at {entry.get('time', 'time unavailable')}",
                ))

        return slides

    def make_f1_calendar_slide(self, entry):
        status = entry.get("status") or "Scheduled"
        time_text = entry.get("time", "time unavailable")
        session = entry.get("session", "Session")
        broadcast = entry.get("broadcast", "")
        message = f"{session} - {status} at {time_text}"
        if broadcast:
            message = f"{message}\nBroadcast: {broadcast}"

        return CarouselMessageCard(
            title=f"{entry.get('label', 'F1')} - {entry.get('name', 'Upcoming event')}",
            message=message,
        )

    def make_f1_live_slides(self, event, config, now):
        slides = []
        live_count = 0
        upcoming_count = 0
        event_name = event.get("shortName", event.get("name", "F1 event"))

        for competition in event.get("competitions", []):
            status = competition.get("status", {})
            state = status.get("type", {}).get("state", "")
            session_time = parse_espn_datetime(
                competition.get("startDate") or competition.get("date") or event.get("date")
            )

            include_session = state == "in"
            if state == "pre" and session_time:
                include_session = now <= session_time <= now + timedelta(hours=24)

            if not include_session:
                continue

            if state == "in":
                live_count += 1
            elif state == "pre":
                upcoming_count += 1

            abbreviation = competition.get("type", {}).get("abbreviation", "")
            session_name = F1_SESSION_LABELS.get(abbreviation, abbreviation or "Session")
            broadcast = competition.get("broadcast", "")
            detail = status.get("type", {}).get("description", "Scheduled")
            time_text = self.format_time_only(session_time) if session_time else "time unavailable"
            message = f"{session_name} - {detail} at {time_text}"
            if broadcast:
                message = f"{message}\nBroadcast: {broadcast}"

            slides.append(CarouselMessageCard(
                title=f"{config['label']} - {event_name}",
                message=message,
            ))

        return slides, live_count, upcoming_count

    def fetch_dashboard_payload(self, sport, league, resource, label):
        use_openf1 = self.is_openf1_selection(sport, league)
        url = build_openf1_url(resource) if use_openf1 else build_url(sport, league, resource)
        self.set_loading_status(f"Loading {label.lower()}", True)

        try:
            data = get_openf1_resource(resource) if use_openf1 else get_resource(sport, league, resource)
        except requests.RequestException as error:
            self.dashboard_debug_payloads[label] = {
                "url": url,
                "path": resource,
                "error": str(error),
            }
            self.set_loading_status(f"{label} failed.", False)
            if hasattr(self, "root_screen"):
                if label == "News":
                    self.render_headline_empty_state(
                        "Headlines unavailable",
                        "The news feed did not return this time. Refresh when the network settles.",
                    )
                elif "scoreboard" in label.lower():
                    self.root_screen.ids.focus_label.text = f"{label} failed"
            return None

        self.dashboard_debug_payloads[label] = {
            "url": url,
            "path": resource,
            "data": data,
        }
        self.set_loading_status(f"Loaded {label.lower()}", False)
        return data

    def fetch_game_summary(self, event_id, sport=None, league=None):
        if not event_id:
            return None

        if event_id in self.game_summary_cache:
            return self.game_summary_cache[event_id]

        sport = sport or self.get_selected_sport()
        league = league or self.get_selected_league()
        resource = f"summary?event={event_id}"
        summary = self.fetch_dashboard_payload(sport, league, resource, f"Game summary {event_id}")
        if summary is not None:
            self.game_summary_cache[event_id] = summary

        return summary

    def get_current_event_id(self, scoreboard):
        if not isinstance(scoreboard, dict):
            return None

        events = scoreboard.get("events", [])
        if not events:
            return None

        for event in events:
            state = event.get("status", {}).get("type", {}).get("state")
            if state == "in":
                return event.get("id")

        now = datetime.now().astimezone()
        for event in events:
            if is_live_or_upcoming_event(event, now):
                return event.get("id")

        return None

    def make_current_game_text(self, summary):
        if not isinstance(summary, dict):
            return "Current game summary unavailable."

        header = summary.get("header", {})
        competitions = header.get("competitions", [])
        status = ""
        if competitions:
            status = competitions[0].get("status", {}).get("type", {}).get("description", "")

        return "\n".join([
            header.get("name", "Current game"),
            status or "Summary loaded",
            f"Boxscore teams: {len(summary.get('boxscore', {}).get('teams', []))}",
            f"Leader sections: {len(summary.get('leaders', []))}",
        ])

    def update_current_game_card(self, summary):
        game_data = self.parse_current_game_summary(summary)
        if self.live_game_slides and isinstance(self.live_game_slides[0], SmallEventCard):
            current_card = self.live_game_slides[0]
            game_data["event_id"] = game_data.get("event_id") or current_card.event_id
            game_data["date_text"] = game_data.get("date_text") or current_card.date_text
            game_data["weather_icon"] = current_card.weather_icon
            game_data["weather_text"] = current_card.weather_text
            game_data["venue_text"] = current_card.venue_text

        if not self.live_game_slides:
            self.live_game_slides = [SmallEventCard(**game_data), self.make_end_slide()]
        else:
            self.live_game_slides[0] = SmallEventCard(**game_data)

        self.live_game_index = 0
        self.now_next_index = 0
        self.render_live_carousel_slide()

    def parse_current_game_summary(self, summary):
        fallback = {
            "event_id": "",
            "title": "Current game",
            "away_abbreviation": "AWAY",
            "away_logo": "",
            "away_score": "-",
            "away_color": [0.95, 0.98, 1, 1],
            "home_abbreviation": "HOME",
            "home_logo": "",
            "home_score": "-",
            "home_color": [0.95, 0.98, 1, 1],
            "date_text": "time unavailable",
            "time_text": "Status unavailable",
            "weather_icon": "",
            "weather_text": "Weather unavailable",
            "venue_text": "",
        }
        if not isinstance(summary, dict):
            return fallback

        header = summary.get("header", {})
        competitions = header.get("competitions", [])
        if not competitions:
            fallback["title"] = header.get("name", fallback["title"])
            return fallback

        competition = competitions[0]
        competitors = competition.get("competitors", [])
        by_side = {}
        for competitor in competitors:
            side = competitor.get("homeAway", "")
            team = competitor.get("team", {})
            by_side[side] = {
                "abbreviation": team.get("abbreviation", "?"),
                "logo": get_team_logo(team),
                "score": str(competitor.get("score", "-")),
                "color": hex_to_rgba(team.get("color", "")),
            }

        status = competition.get("status", {})

        away = by_side.get("away", {})
        home = by_side.get("home", {})
        return {
            "event_id": str(header.get("id", "")),
            "title": header.get("name", "Current game"),
            "away_abbreviation": away.get("abbreviation", fallback["away_abbreviation"]),
            "away_logo": away.get("logo", ""),
            "away_score": away.get("score", "-"),
            "away_color": away.get("color", fallback["away_color"]),
            "home_abbreviation": home.get("abbreviation", fallback["home_abbreviation"]),
            "home_logo": home.get("logo", ""),
            "home_score": home.get("score", "-"),
            "home_color": home.get("color", fallback["home_color"]),
            "date_text": format_event_datetime(competition.get("date")),
            "time_text": format_game_clock(status, competition.get("date")),
            "weather_icon": fallback["weather_icon"],
            "weather_text": fallback["weather_text"],
            "venue_text": fallback["venue_text"],
        }

    def parse_game_from_scoreboard_event(self, event, config=None):
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])
        by_side = {}
        for competitor in competitors:
            side = competitor.get("homeAway", "")
            team = competitor.get("team", {})
            by_side[side] = {
                "abbreviation": team.get("abbreviation", "?"),
                "logo": get_team_logo(team),
                "score": str(competitor.get("score", "-")),
                "color": hex_to_rgba(team.get("color", "")),
            }

        status = event.get("status", {})
        away = by_side.get("away", {})
        home = by_side.get("home", {})
        venue = competition.get("venue", {}) or event.get("venue", {}) or {}
        weather = self.get_weather_for_venue(venue, home.get("abbreviation", ""))

        return {
            "event_id": str(event.get("id", "")),
            "sport_slug": (config or {}).get("sport", ""),
            "league_slug": (config or {}).get("league", ""),
            "title": event.get("name", "Current game"),
            "away_abbreviation": away.get("abbreviation", "AWAY"),
            "away_logo": away.get("logo", ""),
            "away_score": away.get("score", "-"),
            "away_color": away.get("color", [0.95, 0.98, 1, 1]),
            "home_abbreviation": home.get("abbreviation", "HOME"),
            "home_logo": home.get("logo", ""),
            "home_score": home.get("score", "-"),
            "home_color": home.get("color", [0.95, 0.98, 1, 1]),
            "date_text": format_event_datetime(competition.get("date") or event.get("date")),
            "time_text": format_game_clock(status, competition.get("date") or event.get("date")),
            "weather_icon": weather.get("icon", ""),
            "weather_text": weather.get("text", "Weather unavailable"),
            "venue_text": weather.get("venue_text", ""),
        }

    def build_live_game_slides(self, events):
        slides = []
        relevant_events = [event for event in events if is_live_or_upcoming_event(event)]

        for event in relevant_events:
            slides.append(SmallEventCard(**self.parse_game_from_scoreboard_event(event)))

        if not slides:
            slides.append(CarouselMessageCard(
                title="No live or next-24h events",
                message="This feed has no current games or games starting soon.",
            ))

        slides.append(self.make_end_slide())
        self.live_game_slides = slides
        self.live_game_index = 0
        self.now_next_index = 0
        self.render_live_carousel_slide()

    def open_game_detail(self, event_id):
        if not self.unfinished_features_enabled:
            return

        summary = self.fetch_game_summary(event_id)
        if summary is None:
            return

        self.game_summary_cache[event_id] = summary
        self.root_screen.active_view = "game_detail"
        self.render_game_detail(summary)
        self.show_debug_for_current_view()

    def render_game_detail(self, summary):
        ids = self.root_screen.ids
        ids.game_detail_body.clear_widgets()
        ids.game_detail_body.cols = 1

        game_data = self.parse_current_game_summary(summary)
        ids.game_detail_body.add_widget(SmallEventCard(
            size_hint_y=None,
            height=170,
            **game_data,
        ))

        details = self.make_game_detail_text(summary)
        ids.game_detail_body.add_widget(TextInput(
            text=details,
            readonly=True,
            font_size=12,
            background_color=(0.025, 0.035, 0.055, 1),
            foreground_color=(0.95, 0.97, 1.0, 1),
            cursor_color=(0.95, 0.97, 1.0, 1),
        ))

    def make_game_detail_text(self, summary):
        if not isinstance(summary, dict):
            return "No game detail available."

        header = summary.get("header", {})
        boxscore = summary.get("boxscore", {})
        leaders = summary.get("leaders", [])
        drives = summary.get("drives", {})
        competitions = header.get("competitions", [])
        competition = competitions[0] if competitions else {}
        venue = competition.get("venue", {}) or {}
        venue_name = venue.get("fullName", "Venue unavailable")
        address = venue.get("address", {})
        venue_location = ", ".join([
            value for value in [
                address.get("city", ""),
                address.get("state", ""),
                address.get("country", ""),
            ]
            if value
        ])

        lines = [
            header.get("name", "Game detail"),
            "",
            f"Venue: {venue_name}",
            f"Location: {venue_location or 'Location unavailable'}",
            f"Boxscore teams: {len(boxscore.get('teams', []))}",
            f"Leader sections: {len(leaders)}",
        ]

        if isinstance(drives, dict):
            lines.append(f"Drive sections: {', '.join(drives.keys())}")

        if leaders:
            lines.append("")
            lines.append("Leaders:")
            for leader_group in leaders[:5]:
                name = leader_group.get("name", leader_group.get("displayName", "Leader"))
                leaders_items = leader_group.get("leaders", [])
                lines.append(f"- {name}")
                for item in leaders_items[:3]:
                    athlete = item.get("athlete", {})
                    display_value = item.get("displayValue", item.get("value", ""))
                    lines.append(f"  {athlete.get('displayName', 'Unknown')}: {display_value}")

        return "\n".join(lines)

    def get_weather_for_venue(self, venue, fallback_label=""):
        address = venue.get("address", {}) if isinstance(venue, dict) else {}
        city = address.get("city", "")
        state = address.get("state", "")
        country = address.get("country", "")
        location_label = ", ".join([part for part in [city, state or country] if part])
        if not location_label:
            return {
                "icon": "",
                "text": "Weather unavailable",
                "venue_text": fallback_label,
            }

        if location_label in self.weather_cache:
            return self.weather_cache[location_label]

        try:
            geocode = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 10, "language": "en", "format": "json"},
                timeout=8,
            )
            geocode.raise_for_status()
            results = geocode.json().get("results", [])
            if not results:
                raise requests.RequestException("No geocoding results")

            location = self.choose_geocode_result(results, state, country)
            latitude = location["latitude"]
            longitude = location["longitude"]
            weather_response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,weather_code",
                    "temperature_unit": "fahrenheit",
                },
                timeout=8,
            )
            weather_response.raise_for_status()
            current = weather_response.json().get("current", {})
            temp_f = current.get("temperature_2m")
            code = current.get("weather_code")
            temp_c = (float(temp_f) - 32) * 5 / 9 if temp_f is not None else None

            weather = {
                "icon": self.get_weather_icon(code),
                "text": f"{round(temp_f)}F / {round(temp_c)}C - {location_label}" if temp_f is not None and temp_c is not None else f"Weather unavailable - {location_label}",
                "venue_text": location_label,
            }
        except (requests.RequestException, KeyError, TypeError, ValueError):
            weather = {
                "icon": "",
                "text": f"Weather unavailable - {location_label}",
                "venue_text": location_label,
            }

        self.weather_cache[location_label] = weather
        return weather

    def get_projected_weather_for_venue(self, venue, event_time=None, fallback_label=""):
        if not event_time:
            return self.get_weather_for_venue(venue, fallback_label)

        address = venue.get("address", {}) if isinstance(venue, dict) else {}
        city = address.get("city", "")
        state = address.get("state", "")
        country = address.get("country", "")
        location_label = ", ".join([part for part in [city, state or country] if part])
        if not location_label:
            return {
                "icon": "",
                "text": "Weather unavailable",
                "venue_text": fallback_label,
            }

        cache_key = f"forecast:{location_label}:{event_time:%Y-%m-%d-%H}"
        if cache_key in self.weather_cache:
            return self.weather_cache[cache_key]

        try:
            geocode = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 10, "language": "en", "format": "json"},
                timeout=8,
            )
            geocode.raise_for_status()
            results = geocode.json().get("results", [])
            if not results:
                raise requests.RequestException("No geocoding results")

            location = self.choose_geocode_result(results, state, country)
            forecast_response = requests.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "hourly": "temperature_2m,weather_code",
                    "temperature_unit": "fahrenheit",
                    "timezone": "auto",
                    "start_date": event_time.date().isoformat(),
                    "end_date": event_time.date().isoformat(),
                },
                timeout=8,
            )
            forecast_response.raise_for_status()
            hourly = forecast_response.json().get("hourly", {})
            times = hourly.get("time", [])
            temperatures = hourly.get("temperature_2m", [])
            codes = hourly.get("weather_code", [])
            if not times or not temperatures:
                raise requests.RequestException("No hourly forecast")

            target_hour = event_time.hour
            best_index = min(
                range(len(times)),
                key=lambda index: abs(parse_espn_datetime(times[index]).hour - target_hour)
                if parse_espn_datetime(times[index]) else 24,
            )
            temp_f = temperatures[best_index]
            code = codes[best_index] if best_index < len(codes) else None
            temp_c = (float(temp_f) - 32) * 5 / 9 if temp_f is not None else None

            weather = {
                "icon": self.get_weather_icon(code),
                "text": f"{round(temp_f)}F / {round(temp_c)}C - {location_label}" if temp_f is not None and temp_c is not None else f"Weather unavailable - {location_label}",
                "venue_text": location_label,
            }
        except (requests.RequestException, KeyError, TypeError, ValueError):
            weather = {
                "icon": "",
                "text": f"Forecast not available yet - {location_label}",
                "venue_text": location_label,
            }

        self.weather_cache[cache_key] = weather
        return weather

    def choose_geocode_result(self, results, state, country):
        if not results:
            raise requests.RequestException("No geocoding results")

        country = (country or "").upper()
        state = state or ""
        for result in results:
            country_match = country in ("", result.get("country_code", "").upper(), result.get("country", "").upper())
            state_match = state in ("", result.get("admin1", ""), result.get("admin2", ""))
            if country_match and state_match:
                return result

        for result in results:
            if country == "USA" and result.get("country_code") == "US":
                return result

        return results[0]

    def get_weather_icon(self, code):
        if code is None:
            return ""
        if code in (0, 1):
            return "sun"
        if code in (2, 3, 45, 48):
            return "cloud"
        if 51 <= code <= 67 or 80 <= code <= 82:
            return "rain"
        if 71 <= code <= 77 or 85 <= code <= 86:
            return "snow"
        if 95 <= code <= 99:
            return "storm"
        return "cloud"

    def on_dropdown_changed(self, favorite_key):
        if favorite_key == "sports":
            self.load_leagues()
            return

        if favorite_key == "leagues":
            self.load_teams()
            return

        if favorite_key in ("resources", "teams"):
            self.sync_path_from_controls()

        self.update_url_preview()

    def get_selected_sport(self):
        return self.sport_dropdown.text

    def get_selected_league(self):
        return self.league_dropdown.text

    def get_selected_resource_path(self):
        return self.resource_path_input.text.strip().strip("/") or "scoreboard"

    def get_current_url(self):
        if self.is_openf1_selection():
            return build_openf1_url(self.get_selected_resource_path())

        return build_url(
            self.get_selected_sport(),
            self.get_selected_league(),
            self.get_selected_resource_path(),
        )

    def is_openf1_selection(self, sport=None, league=None):
        sport = sport or self.get_selected_sport()
        league = league or self.get_selected_league()
        return sport == "racing" and league == "f1"

    def sync_path_from_controls(self):
        resource = RESOURCES[self.resource_dropdown.text]

        if resource == "team":
            selected_team = self.team_dropdown.text
            team_slug = self.team_options.get(selected_team)
            if team_slug:
                self.set_resource_path(f"teams/{team_slug}", False)
            else:
                self.set_resource_path("teams", False)
            return

        self.set_resource_path(resource, False)

    def set_resource_path(self, resource, fetch_after=False):
        self.resource_path_input.text = resource.strip().strip("/") or "scoreboard"
        self.update_resource_controls_from_path()
        self.update_url_preview()
        self.log_debug(f"Path set to: {self.get_selected_resource_path()}")

        if fetch_after:
            self.fetch_resource()

    def update_resource_controls_from_path(self):
        path = self.get_selected_resource_path()

        if path.startswith("scoreboard"):
            self.resource_dropdown.set_text("Scoreboard")
        elif path == "teams":
            self.resource_dropdown.set_text("Teams")
            self.team_dropdown.set_text("All teams")
        elif path.startswith("teams/"):
            self.resource_dropdown.set_text("Team details")
        elif path.startswith("news"):
            self.resource_dropdown.set_text("News")

    def update_url_preview(self):
        self.url_label.text = f"Built URL:\n{self.get_current_url()}"
        if hasattr(self, "root_screen"):
            self.set_loading_status(f"Ready: {self.get_selected_resource_path()}", False)

    def load_sports(self):
        self.log_debug("Loading sports from ESPN Core API.")
        try:
            sports = get_sports()
        except requests.RequestException as error:
            self.log_debug(f"Sports request failed, using fallback: {error}")
            sports = FALLBACK_SPORTS

        if not sports:
            self.log_debug("Sports request returned no items, using fallback.")
            sports = FALLBACK_SPORTS

        self.update_dropdown_values(self.sport_dropdown, sports, "sports")
        if DEFAULT_SPORT in sports:
            self.sport_dropdown.set_text(DEFAULT_SPORT)
        else:
            self.sport_dropdown.set_text(sports[0])

        self.load_leagues()

    def load_leagues(self):
        sport = self.get_selected_sport()
        self.log_debug(f"Loading leagues for sport: {sport}")

        try:
            leagues = get_leagues(sport)
        except requests.RequestException as error:
            self.log_debug(f"League request failed, using fallback: {error}")
            leagues = FALLBACK_LEAGUES.get(sport, [])

        if not leagues:
            self.log_debug("League request returned no items, using fallback.")
            leagues = FALLBACK_LEAGUES.get(sport, [])

        self.update_dropdown_values(self.league_dropdown, leagues, "leagues")
        if DEFAULT_LEAGUE in leagues:
            self.league_dropdown.set_text(DEFAULT_LEAGUE)
        elif leagues:
            self.league_dropdown.set_text(leagues[0])

        self.load_teams()

    def write_output(self, text):
        self.output.text = text

    def load_teams(self):
        sport = self.get_selected_sport()
        league = self.get_selected_league()

        if self.is_openf1_selection(sport, league):
            self.team_dropdown.set_text("OpenF1 sessions")
            self.team_dropdown.set_values(["OpenF1 sessions"])
            self.team_options = {}
            self.set_resource_path("sessions", False)
            self.log_debug("F1 uses OpenF1 endpoints; team lookup is disabled.")
            return

        self.team_dropdown.set_text("Loading teams...")
        self.team_dropdown.set_values(["Loading teams..."])
        self.team_options = {}
        self.update_url_preview()
        self.log_debug(f"Loading teams for {sport}/{league}.")

        try:
            data = get_resource(sport, league, "teams")
        except requests.RequestException as error:
            self.team_dropdown.set_text("All teams")
            self.team_dropdown.set_values(["All teams"])
            self.log_debug(f"Team request failed: {error}")
            return

        team_labels = ["All teams"]
        self.team_options = {}

        teams = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
        for team_wrapper in teams:
            team = team_wrapper.get("team", {})
            abbreviation = team.get("abbreviation", "")
            display_name = team.get("displayName", "Unknown team")
            slug = team.get("abbreviation", "").lower()
            label = f"{abbreviation} - {display_name}"

            team_labels.append(label)
            self.team_options[label] = slug

        self.team_dropdown.set_text("All teams")
        self.update_dropdown_values(self.team_dropdown, team_labels, "teams")
        self.sync_path_from_controls()
        self.update_url_preview()
        self.log_debug(f"Loaded {len(teams)} teams.")

    def fetch_resource(self):
        sport = self.get_selected_sport()
        league = self.get_selected_league()
        resource = self.get_selected_resource_path()
        url = self.get_current_url()

        self.update_url_preview()
        self.write_output(f"Fetching:\n{url}\n")
        self.log_debug(f"Request started: sport={sport}, league={league}, path={resource}")
        if hasattr(self, "root_screen"):
            self.set_loading_status(f"Fetching {resource}", True)

        try:
            if self.is_openf1_selection(sport, league):
                data = get_openf1_resource(resource)
            else:
                data = get_resource(sport, league, resource)
        except requests.RequestException as error:
            self.write_output(f"Request failed:\n{error}")
            self.log_debug(f"Request failed: {error}")
            if hasattr(self, "root_screen"):
                self.set_loading_status("Request failed.", False)
            return

        preview = self.render_openf1_preview(resource, data) if self.is_openf1_selection(sport, league) else render_site_v2_preview(resource, data)
        self.write_output(f"URL:\n{url}\n\n{preview}")
        self.write_debug_snapshot(url, resource, data)
        self.update_dashboard_summary(resource, data)

    def render_openf1_preview(self, resource, data):
        rows = data if isinstance(data, list) else []
        lines = [
            "OpenF1 response",
            f"Endpoint: {resource}",
            f"Rows: {len(rows)}",
            "",
        ]

        if rows:
            lines.append("First item:")
            lines.append(json.dumps(rows[0], indent=2)[:2500])
        else:
            lines.append(json.dumps(data, indent=2)[:2500])

        return "\n".join(lines)

    def write_debug_snapshot(self, url, resource, data):
        self.api_debug_payload = {
            "url": url,
            "path": resource,
            "data": data,
        }
        if isinstance(data, dict):
            keys = ", ".join(list(data.keys())[:20])
            raw_sample = json.dumps(data, indent=2)[:4000]
            size_hint = f"{len(json.dumps(data))} JSON chars"
        else:
            keys = type(data).__name__
            raw_sample = json.dumps(data, indent=2)[:4000]
            size_hint = "non-dict response"

        self.debug_output.text = "\n".join([
            "DEBUG SNAPSHOT",
            f"URL: {url}",
            f"Path: {resource}",
            f"Response: {size_hint}",
            f"Keys: {keys}",
            "",
            "Raw JSON sample:",
            raw_sample,
        ])
        if hasattr(self, "root_screen"):
            self.set_loading_status(f"Loaded {resource}", False)
            self.show_debug_for_current_view()

    def show_debug_for_current_view(self):
        if not hasattr(self, "debug_output") or not hasattr(self, "root_screen"):
            return

        active_view = self.root_screen.active_view
        if active_view == "api":
            self.debug_output.text = self.render_single_debug_payload(
                "API EXPLORER DEBUG",
                self.api_debug_payload,
                fallback="No API Explorer request has been fetched yet.",
            )
            return

        if active_view == "home":
            self.debug_output.text = self.render_dashboard_debug()
            return

        self.debug_output.text = "\n".join([
            f"{active_view.upper()} DEBUG",
            "No dedicated API feed is wired to this window yet.",
            "",
            "Dashboard feed cache:",
            self.render_payload_index(self.dashboard_debug_payloads),
        ])

    def render_dashboard_debug(self):
        if not self.dashboard_debug_payloads:
            return "DASHBOARD DEBUG\nNo dashboard feeds have been fetched yet."

        sections = [
            "DASHBOARD DEBUG",
            "These are the API responses feeding the current Dashboard window.",
        ]
        for label in ["Scoreboard", "News", "Current game summary"]:
            payload = self.dashboard_debug_payloads.get(label)
            if payload:
                sections.append("")
                sections.append(self.render_single_debug_payload(label.upper(), payload))

        return "\n".join(sections)

    def render_single_debug_payload(self, title, payload, fallback="No payload available."):
        if not payload:
            return f"{title}\n{fallback}"

        lines = [
            title,
            f"URL: {payload.get('url', 'Unknown URL')}",
            f"Path: {payload.get('path', 'Unknown path')}",
        ]

        if payload.get("error"):
            lines.extend(["", f"Error: {payload['error']}"])
            return "\n".join(lines)

        data = payload.get("data")
        if isinstance(data, dict):
            raw_json = json.dumps(data, indent=2)
            lines.extend([
                f"Response: {len(raw_json)} JSON chars",
                f"Keys: {', '.join(list(data.keys())[:20])}",
                "",
                "Raw JSON sample:",
                raw_json[:2500],
            ])
        else:
            lines.extend([
                f"Response type: {type(data).__name__}",
                "",
                "Raw JSON sample:",
                json.dumps(data, indent=2)[:2500],
            ])

        return "\n".join(lines)

    def render_payload_index(self, payloads):
        if not payloads:
            return "  No cached payloads."

        lines = []
        for label, payload in payloads.items():
            status = "error" if payload.get("error") else "loaded"
            lines.append(f"  - {label}: {status} ({payload.get('path', '?')})")

        return "\n".join(lines)

    def update_dashboard_summary(self, resource, data):
        if not hasattr(self, "root_screen"):
            return

        ids = self.root_screen.ids
        if resource.startswith("scoreboard") and isinstance(data, dict):
            events = data.get("events", [])
            relevant_events = [event for event in events if is_live_or_upcoming_event(event)]
            live_count = sum(
                1
                for event in relevant_events
                if event.get("status", {}).get("type", {}).get("state") == "in"
            )
            upcoming_count = sum(
                1
                for event in relevant_events
                if event.get("status", {}).get("type", {}).get("state") == "pre"
            )
            today_count, next_label = self.get_scoreboard_today_details(events)
            self.render_today_summary(
                live=live_count,
                today=today_count,
                upcoming=upcoming_count,
                next_label=next_label,
            )
            ids.focus_label.text = f"{self.get_selected_league().upper()} - {live_count} live, {upcoming_count} next 24h"
            if events:
                self.build_live_game_slides(events)
            else:
                self.live_game_slides = [
                    CarouselMessageCard(
                        title="No games found",
                        message="Try another date, league, or sport.",
                    ),
                    self.make_end_slide(),
                ]
                self.live_game_index = 0
                self.now_next_index = 0
                self.render_live_carousel_slide()
        elif resource.startswith("news") and isinstance(data, dict):
            articles = data.get("articles", [])
            self.headline_articles = articles[:12]
            self.headline_index = 0
            if not articles:
                self.render_headline_empty_state(
                    "No headlines found",
                    "The selected feed returned no articles.",
                )
                ids.last_updated.text = "Updated just now"
                return

            self.render_headline_cards()
        elif isinstance(data, dict):
            ids.focus_label.text = f"{self.get_selected_sport()} / {self.get_selected_league()}"

        ids.last_updated.text = "Updated just now"

    def get_scoreboard_today_details(self, events):
        now = datetime.now().astimezone()
        today_count = 0
        next_time = None

        for event in events:
            event_time = parse_espn_datetime(event.get("date"))
            if not event_time:
                continue
            if event_time.date() == now.date():
                today_count += 1
            if event_time >= now and (next_time is None or event_time < next_time):
                next_time = event_time

        return today_count, self.format_next_start_label(next_time, now)

    def log_debug(self, message):
        if not hasattr(self, "debug_output"):
            return

        existing = self.debug_output.text
        if existing == "Debug log ready.":
            existing = ""

        self.debug_output.text = f"{existing}\n{message}".strip()

    def toggle_debug_panel(self):
        if self.debug_expanded:
            self.root_screen.debug_open = False
            self.debug_toggle.text = "Show Debug"
            self.debug_expanded = False
            return

        self.show_debug_for_current_view()
        self.root_screen.debug_open = True
        self.debug_toggle.text = "Hide Debug"
        self.debug_expanded = True


if __name__ == "__main__":
    NashTrackApp().run()
