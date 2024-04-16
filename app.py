from flask import Flask, render_template
import requests

app = Flask(__name__)

API_KEY = "RGAPI-bdc4ed7a-df65-408f-a12b-73e5aa23303e"

BASE_URL = "https://eun1.api.riotgames.com"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summoner')
def summoner():
    summoner_name = "Peprný kotoul"
    endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"
    url = BASE_URL + endpoint
    headers = {
        "X-Riot-Token": API_KEY
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return render_template('summoner.html', summoner_data=data, summoner_name=summoner_name)
    else:
        error_message = f"Error: {response.status_code}"
        return render_template('summoner.html', error=error_message)


@app.route('/ranked')
def ranked():
    encryptedSummonerId = "ux5iNhCX9pHOyOepp4914QwEq_iIJ2tioPhKGiDNhkWPKe0"
    endpoint = f"/lol/league/v4/entries/by-summoner/{encryptedSummonerId}"
    url = BASE_URL + endpoint
    headers = {
        "X-Riot-Token": API_KEY
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(data)
        return render_template('ranked.html', soloq_data=data[0], flex_data=data[1])
    else:
        error_message = f"Error: {response.status_code}"
        return render_template('ranked.html', error=error_message)


@app.route('/challenger')
def challenger():
    queue = "RANKED_SOLO_5x5"
    endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"
    url = BASE_URL + endpoint
    headers = {
        "X-Riot-Token": API_KEY
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(data)
        return render_template('challenger.html', data=data)
    else:
        error_message = f"Error: {response.status_code}"
        return render_template('challenger.html', error=error_message)


if __name__ == '__main__':
    app.run(debug=True)
