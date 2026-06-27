from urllib.parse import urlencode

import requests


BASE_URL = "https://api.openf1.org/v1"


def build_url(endpoint, params=None):
    endpoint = endpoint.strip().strip("/")
    url = f"{BASE_URL}/{endpoint}"
    if params:
        clean_params = {
            key: value
            for key, value in params.items()
            if value is not None and value != ""
        }
        if clean_params:
            url = f"{url}?{urlencode(clean_params)}"
    return url


def get_resource(endpoint, params=None):
    url = build_url(endpoint, params)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


def get_sessions(year=None):
    params = {}
    if year:
        params["year"] = year
    return get_resource("sessions", params)
