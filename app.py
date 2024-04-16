from flask import Flask, render_template
import requests

app = Flask(__name__)

API_KEY = "RGAPI-bdc4ed7a-df65-408f-a12b-73e5aa23303e"

BASE_URL = "https://eun1.api.riotgames.com"


@app.route('/')
def index():
    summoner_name = "Peprný kotoul"
    endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"
    url = BASE_URL + endpoint
    headers = {
        "X-Riot-Token": API_KEY
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return render_template('index.html', summoner_data=data, summoner_name=summoner_name)
    else:
        error_message = f"Error: {response.status_code}"
        return render_template('index.html', error=error_message)


if __name__ == '__main__':
    app.run(debug=True)
