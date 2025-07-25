
import logging

from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix
from python_server.shared.constants import GREEN, RED, GOLD, WHITE
from python_server.shared.service.football_service import *
def run(stop_event):
    stop_scrolling_text()
    display_live_scores(stop_event)
    display_today_matches(stop_event)
    #stop_scrolling_text()


def display_live_scores(stop_event):
    matches = get_live_scores()
    display_on_matrix("Live Scores:\n", GREEN,stop_event)
    if matches['count'] > 0:
        for match in matches['matches']:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            home_score = match['score']['fullTime']['homeTeam']
            away_score = match['score']['fullTime']['awayTeam']
            competition = match['competition']['name']
            display_on_matrix(f"{home_team} {home_score} - {away_team} {away_score} ({competition})", GOLD,stop_event)
    else:
        display_on_matrix("No live matches at the moment.",RED,stop_event)


def display_today_matches(stop_event):
    matches = get_today_matches()
    display_on_matrix("Today's Matches:", GOLD,stop_event)
    if matches['count'] > 0:
        for match in matches['matches']:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            competition = match['competition']['name']
            match_time = match['utcDate']
            display_on_matrix(f"{home_team} vs {away_team} ({competition}) at {match_time}", WHITE,stop_event)
    else:
        display_today_matches("No matches scheduled for today.", RED,stop_event)


def display_league_standings(league_code):
    standings = get_league_standings(league_code)
    competition_name = standings.get('competition', {}).get('name', 'Unknown Competition')
    logging.info(f"Standings for {competition_name}:\n")

    for table in standings['standings']:
        group = table.get('group', 'Unknown Group')
        logging.info(f"\n{group} Standings:")
        for team in table['table']:
            position = team.get('position', 'N/A')
            team_name = team.get('team', {}).get('name', 'Unknown Team')
            points = team.get('points', 'N/A')
            logging.info(f"{position}: {team_name} - {points} points")

def display_team_fixtures(team_id):
    fixtures = get_team_fixtures(team_id)
    # Process and display fixtures data
    for match in fixtures['matches']:
        logging.info(f"{match['utcDate']}: {match['homeTeam']['name']} vs {match['awayTeam']['name']}")

def display_match_details(match_id):
    match = get_match_details(match_id)
    # Process and display match details
    logging.info(f"Match: {match['match']['homeTeam']['name']} vs {match['match']['awayTeam']['name']}")
    logging.info(f"Score: {match['match']['score']['fullTime']['homeTeam']} - {match['match']['score']['fullTime']['awayTeam']}")


