import requests
import json

API_KEY = "RGAPI-fcdbcccb-02a6-4a5c-898a-d134d3940bab"

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
        return data['gameName']
    else:
        error_message = f"Error: {response.status_code}"
        return error_message


def get_puuid_by_id(encryptedSummonerId):
    endpoint = f"/lol/summoner/v4/summoners/{encryptedSummonerId}"
    url = EUN1_URL + endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data['puuid']
    else:
        error_message = f"Error: {response.status_code}"
        return error_message


def change_id_to_name(data):
    puuids = []
    names = []
    for i in range(len(data)):
        puuids.append(get_puuid_by_id(data[i]['summonerId']))
        names.append(get_name_by_puuid(puuids[i]))
        data[i]['playerName'] = names[i]
        print(data[i]['playerName'])
    return data


def load_challengers(starting_number):
    players = []
    queue = "RANKED_SOLO_5x5"
    endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"
    if error(endpoint):
        print(error)
    else:
        players = get_api_data(endpoint)
        players = players['entries']
        players = sorted(players, key=lambda x: -x['leaguePoints'])
        players = change_id_to_name(players[starting_number:starting_number + 50])
