import requests

API_KEY = "RGAPI-a2b67eec-0ecb-49ba-848b-03cd27ffb7fb"

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


def get_api_data_by_region(endpoint):
    url = EUROPE_CLUSTER_URL + endpoint

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


def error_by_region(endpoint):
    url = EUROPE_CLUSTER_URL + endpoint
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
        print(data['gameName'])
        return data['gameName']
    else:
        return None


def get_puuid_by_id(encryptedSummonerId):
    endpoint = f"/lol/summoner/v4/summoners/{encryptedSummonerId}"
    url = EUN1_URL + endpoint
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        print(data['puuid'])
        return data['puuid']
    else:
        return None
