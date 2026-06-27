import requests


BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"


def build_url(sport, league, resource):
    sport = sport.strip().strip("/")
    league = league.strip().strip("/")
    resource = resource.strip().strip("/")

    return f"{BASE_URL}/{sport}/{league}/{resource}"


def get_resource(sport, league, resource):
    url = build_url(sport, league, resource)
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    return response.json()
