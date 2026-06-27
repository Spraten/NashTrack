import json
from pathlib import Path


FAVORITES_PATH = Path(__file__).resolve().parent.parent / "data" / "favorites.json"
DEFAULT_FAVORITES = {
    "sports": [],
    "leagues": [],
    "resources": [],
    "teams": [],
}


def load_favorites():
    if not FAVORITES_PATH.exists():
        return DEFAULT_FAVORITES.copy()

    try:
        with FAVORITES_PATH.open("r", encoding="utf-8") as file:
            favorites = json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_FAVORITES.copy()

    clean_favorites = DEFAULT_FAVORITES.copy()
    for key in clean_favorites:
        clean_favorites[key] = list(favorites.get(key, []))

    return clean_favorites


def save_favorites(favorites):
    FAVORITES_PATH.parent.mkdir(parents=True, exist_ok=True)

    with FAVORITES_PATH.open("w", encoding="utf-8") as file:
        json.dump(favorites, file, indent=2)


def sort_with_favorites(values, favorites):
    favorite_values = [value for value in favorites if value in values]
    regular_values = [value for value in values if value not in favorite_values]

    return favorite_values + regular_values
