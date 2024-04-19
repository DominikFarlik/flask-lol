from flask import Flask, render_template, request, redirect, url_for
from functions import error, get_api_data, get_name_by_puuid, get_puuid_by_id, load_puuids_to_file_from_ids

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/processInput', methods=['POST', 'GET'])
def processInput():
    input_data = request.form['userInput']

    if input_data:
        endpoint = f"/lol/summoner/v4/summoners/by-name/{input_data}"

    return redirect(url_for('summoner', summoner_name=input_data))


@app.route('/summoner/<summoner_name>')
def summoner(summoner_name):
    endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"

    if error(endpoint):
        return render_template('summoner.html', error=get_api_data(endpoint))
    else:
        player_data = get_api_data(endpoint)
        endpoint = f"/lol/league/v4/entries/by-summoner/{player_data['id']}"
        if error(endpoint):
            return render_template('summoner.html', error=get_api_data(endpoint))
        else:
            ranked_data = get_api_data(endpoint)
            print(ranked_data)
            soloq_data = []
            flex_data = []
            solo_winrate = 0
            flex_winrate = 0
            for i in range(len(ranked_data)):
                if ranked_data[i]['queueType'] == 'RANKED_SOLO_5x5':
                    soloq_data = ranked_data[i]
                elif ranked_data[i]['queueType'] == 'RANKED_FLEX_SR':
                    flex_data = ranked_data[i]
            if soloq_data:
                solo_winrate = round((soloq_data['wins'] / (soloq_data['wins'] + soloq_data['losses'])) * 100, 1)
            if flex_data:
                flex_winrate = round((flex_data['wins'] / (flex_data['wins'] + flex_data['losses'])) * 100, 1)
            return render_template('summoner.html', player_data=player_data, summoner_name=summoner_name,
                                   soloq_data=soloq_data, flex_data=flex_data, solo_winrate=solo_winrate, flex_winrate=flex_winrate)


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
