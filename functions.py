import requests
import json

API_KEY = "RGAPI-abe5b2fa-ee3c-46f4-b515-732827d4c186"

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

def load_puuids_to_file_from_ids(data):
    chall_puuids = []
    for i in data:
        chall_puuids.append(get_puuid_by_id(i['summonerId']))

    json_chall_puuids = json.dumps(chall_puuids, indent=4)
    with open("chall_puuids.json", "w") as outfile:
        outfile.write(json_chall_puuids)