from flask import Flask, render_template, request, redirect, url_for, jsonify
from functions import calculate_winrate, convert_epoch_to_duration
from api_functions import error, get_api_data, get_api_data_by_region, error_by_region
from db_functions import find_document_without_puuid, add_missing_puuids, get_collection

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/players', methods=['GET'])
def get_players():
    players = list(get_collection("players").find({}, {"_id": 0}))
    return jsonify(players), 200


@app.route('/processInput', methods=['POST', 'GET'])
def processInput():
    input_data = request.form['userInput']

    if input_data:
        return redirect(url_for('summoner', summoner_name=input_data))


@app.route('/summoner/<summoner_name>')
def summoner(summoner_name):
    # variables for html
    rank_error = ""
    match_history_error = ""
    match_history_data = []
    solo_data = []
    flex_data = []
    solo_winrate = 0
    flex_winrate = 0

    # getting summoner level and icon
    endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"
    if error(endpoint):
        return render_template('summoner.html', player_data_error=get_api_data(endpoint))
    else:
        player_data = get_api_data(endpoint)

    # getting information about player rank statistics
    endpoint = f"/lol/league/v4/entries/by-summoner/{player_data['id']}"
    if error(endpoint):
        rank_error = get_api_data(endpoint)
    else:
        ranked_data = get_api_data(endpoint)
        for i in range(len(ranked_data)):
            if ranked_data[i]['queueType'] == 'RANKED_SOLO_5x5':
                solo_data = ranked_data[i]
            elif ranked_data[i]['queueType'] == 'RANKED_FLEX_SR':
                flex_data = ranked_data[i]
        if solo_data:
            solo_winrate = calculate_winrate(solo_data)
        if flex_data:
            flex_winrate = calculate_winrate(flex_data)

    # getting player matches
    endpoint = f"/lol/match/v5/matches/by-puuid/{player_data['puuid']}/ids"
    if error_by_region(endpoint):
        match_history_error = get_api_data_by_region(endpoint)
    else:
        data = get_api_data_by_region(endpoint)
        for matchId in data:
            match_history_data.append(get_api_data_by_region(f"/lol/match/v5/matches/{matchId}"))
        for i in match_history_data:
            i['info']['gameDuration'] = convert_epoch_to_duration(i['info']['gameDuration'])

    return render_template('summoner.html',
                           player_data=player_data,
                           summoner_name=summoner_name,
                           soloq_data=solo_data,
                           flex_data=flex_data,
                           solo_winrate=solo_winrate,
                           flex_winrate=flex_winrate,
                           rank_error=rank_error,
                           match_history_error=match_history_error,
                           match_history_data=match_history_data)


@app.route('/challenger', methods=['GET', 'POST'])
def challenger():
    queue = "RANKED_SOLO_5x5"
    endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"

    if error(endpoint):
        return render_template('challenger.html', error=get_api_data(endpoint))
    else:
        api_data = get_api_data(endpoint)

    entries = api_data['entries']

    data = [{key: x[key] for key in ['summonerId', 'leaguePoints', 'wins', 'losses']} for x in entries]

    # players_collection.insert_many(data)

    data_without_puuid = find_document_without_puuid()
    add_missing_puuids(data_without_puuid)

    data = sorted(data, key=lambda x: -x['leaguePoints'])

    return render_template('challenger.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
