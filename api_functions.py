import requests

API_KEY = "RGAPI-00ec5a3a-8aee-4b0a-92b8-9dbff2dd6be3"

HEADERS = {"X-Riot-Token": API_KEY}

EUN1_URL = "https://eun1.api.riotgames.com"

EUROPE_CLUSTER_URL = "https://europe.api.riotgames.com"


def handle_api_call(endpoint, type):
    api_data, error_message = "", ""
    if type == "region":
        api_data, error_message = get_api_data_by_region(endpoint)
    elif type == "server":
        api_data, error_message = get_api_data(endpoint)
    return api_data, error_message


def get_api_data(endpoint):
    url = EUN1_URL + endpoint
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json(), None
    else:
        error_message = f"Error: {response.status_code}"
        return None, error_message


def get_api_data_by_region(endpoint):
    url = EUROPE_CLUSTER_URL + endpoint
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json(), None
    else:
        error_message = f"Error: {response.status_code}"
        return None, error_message


def error(endpoint):
    url = EUN1_URL + endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return False
    else:
        return True


def error_by_region(endpoint):
    url = EUROPE_CLUSTER_URL + endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return False
    else:
        return True


def get_name_and_tagline_by_puuid(puuid):
    endpoint = f"/riot/account/v1/accounts/by-puuid/{puuid}"
    url = EUROPE_CLUSTER_URL + endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None


def get_puuid_by_id(encryptedSummonerId):
    endpoint = f"/lol/summoner/v4/summoners/{encryptedSummonerId}"
    url = EUN1_URL + endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        return data['puuid']
    else:
        return None


def get_matches(puuid):
    match_id_endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
    url = EUROPE_CLUSTER_URL + match_id_endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        match_ids = response.json()
        return match_ids
    else:
        return None
