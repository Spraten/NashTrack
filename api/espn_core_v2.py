import requests


BASE_URL = "https://sports.core.api.espn.com/v2/sports"


def get_json(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    return response.json()


def get_slug_from_ref(item):
    ref = item.get("$ref", "")
    path = ref.split("?")[0]

    return path.rstrip("/").split("/")[-1]


def get_sports():
    data = get_json(f"{BASE_URL}?limit=100")
    sports = []

    for item in data.get("items", []):
        slug = get_slug_from_ref(item)
        if slug:
            sports.append(slug)

    return sports


def get_leagues(sport):
    sport = sport.strip().strip("/")
    data = get_json(f"{BASE_URL}/{sport}/leagues?limit=100")
    leagues = []

    for item in data.get("items", []):
        slug = get_slug_from_ref(item)
        if slug:
            leagues.append(slug)

    return leagues
