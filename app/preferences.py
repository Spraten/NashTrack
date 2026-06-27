import json
from pathlib import Path


PREFERENCES_PATH = Path(__file__).resolve().parent.parent / "data" / "preferences.json"
DEFAULT_PREFERENCES = {
    "home_sports": ["NFL", "F1"],
    "dashboard_modules": ["today_summary", "now_next", "headlines", "right_calendar"],
}


def load_preferences():
    if not PREFERENCES_PATH.exists():
        return DEFAULT_PREFERENCES.copy()

    try:
        with PREFERENCES_PATH.open("r", encoding="utf-8") as file:
            preferences = json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PREFERENCES.copy()

    clean_preferences = DEFAULT_PREFERENCES.copy()
    clean_preferences["home_sports"] = [
        sport
        for sport in preferences.get("home_sports", DEFAULT_PREFERENCES["home_sports"])
        if isinstance(sport, str)
    ]
    clean_preferences["dashboard_modules"] = [
        module
        for module in preferences.get("dashboard_modules", DEFAULT_PREFERENCES["dashboard_modules"])
        if isinstance(module, str)
    ]
    return clean_preferences


def save_preferences(preferences):
    PREFERENCES_PATH.parent.mkdir(parents=True, exist_ok=True)

    with PREFERENCES_PATH.open("w", encoding="utf-8") as file:
        json.dump(preferences, file, indent=2)
