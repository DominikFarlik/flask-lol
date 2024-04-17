from flask import Flask, render_template
from functions import error, get_api_data, get_name_by_puuid

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summoner')
def summoner():
    summoner_name = "Peprný kotoul"
    encryptedSummonerId = "ux5iNhCX9pHOyOepp4914QwEq_iIJ2tioPhKGiDNhkWPKe0"
    endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"

    if error(endpoint):
        return render_template('summoner.html', error=get_api_data(endpoint))
    else:
        endpoint = f"/lol/league/v4/entries/by-summoner/{encryptedSummonerId}"

        player_data = get_api_data(endpoint)
        return render_template('summoner.html', player_data=player_data, summoner_name=summoner_name)



    if error(endpoint):
        return render_template('ranked.html', error=get_api_data(endpoint))
    else:
        data = get_api_data(endpoint)
        print(data)
        return render_template('ranked.html', soloq_data=data[0], flex_data=data[1])


@app.route('/challenger')
def challenger():
    queue = "RANKED_SOLO_5x5"
    endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"

    if error(endpoint):
        return render_template('challenger.html', error=get_api_data(endpoint))
    else:
        data = get_api_data(endpoint)
        return render_template('challenger.html', data=data['entries'])


if __name__ == '__main__':
    app.run(debug=True)
