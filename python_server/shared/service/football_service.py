import requests
from datetime import datetime

from python_server.shared.constants import FOOTBALL_BASE_URL
from python_server.shared.service.secret import FOOTBALL_API_TOKEN



def get_headers():
    return {
        'X-Auth-Token': FOOTBALL_API_TOKEN
    }

def get_today_matches():
    today = datetime.today().strftime('%Y-%m-%d')
    url = f'{FOOTBALL_BASE_URL}matches'
    params = {'dateFrom': today, 'dateTo': today}
    response = requests.get(url, headers=get_headers(), params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_live_scores():
    url = f'{FOOTBALL_BASE_URL}matches'
    params = {'status': 'LIVE'}
    response = requests.get(url, headers=get_headers(), params=params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def get_league_standings(league_code):
    url = f'{FOOTBALL_BASE_URL}competitions/{league_code}/standings'
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_team_fixtures(team_id):
    url = f'{FOOTBALL_BASE_URL}teams/{team_id}/matches'
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def get_match_details(match_id):
    url = f'{FOOTBALL_BASE_URL}matches/{match_id}'
    response = requests.get(url, headers=get_headers())
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()