from flask import Flask, render_template, request
from functions import error, get_api_data, get_name_by_puuid, get_puuid_by_id, load_puuids_to_file_from_ids

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/processInput', methods=['POST', 'GET'])
def processInput():
    input_data = request.form['userInput']

    if input_data:
        processed_data = f"You entered: {input_data}"
    else:
        processed_data = "You didn't enter anything!"

    return render_template('summoner.html', result=processed_data)


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


@app.route('/challenger', methods=['GET', 'POST'])
async def challenger():
    queue = "RANKED_SOLO_5x5"
    endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"

    if error(endpoint):
        return render_template('challenger.html', error=get_api_data(endpoint))
    else:
        data = get_api_data(endpoint)
        data = data['entries']
        data = sorted(data, key=lambda x: -x['leaguePoints'])
        #load_puuids_to_file_from_ids(data)

        return render_template('challenger.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
