import requests
from flask import render_template

API_KEY = "RGAPI-bdc4ed7a-df65-408f-a12b-73e5aa23303e"

HEADERS = {"X-Riot-Token": API_KEY}

EUN1_URL = "https://eun1.api.riotgames.com"

EUROPE_CLUSTER_URL = "https://europe.api.riotgames.com"


def get_api_data(endpoint):
    url = EUN1_URL + endpoint

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        error_message = f"Error: {response.status_code}"
        return error_message


def error(endpoint):
    url = EUN1_URL + endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return False
    else:
        return True


def get_name_by_puuid(puuid):
    endpoint = f"/riot/account/v1/accounts/by-puuid/{puuid}"
    url = EUROPE_CLUSTER_URL + endpoint

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        error_message = f"Error: {response.status_code}"
        return error_message
