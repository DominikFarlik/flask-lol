from flask import Flask, render_template
from functions import error, get_api_data, get_name_by_puuid, get_puuid_by_id, change_id_to_name, load_challengers

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
        player_data = get_api_data(endpoint)
        endpoint = f"/lol/league/v4/entries/by-summoner/{encryptedSummonerId}"
        if error(endpoint):
            return render_template('summoner.html', error=get_api_data(endpoint))
        else:
            ranked_data = get_api_data(endpoint)
            return render_template('summoner.html', player_data=player_data, summoner_name=summoner_name,
                                   soloq_data=ranked_data[1], flex_data=ranked_data[0])


@app.route('/challenger')
async def challenger():
    queue = "RANKED_SOLO_5x5"
    endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"

    if error(endpoint):
        return render_template('challenger.html', error=get_api_data(endpoint))
    else:
        data = get_api_data(endpoint)
        data = data['entries']
        data = sorted(data, key=lambda x: -x['leaguePoints'])
        #data = change_id_to_name(data)
        return render_template('challenger.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
