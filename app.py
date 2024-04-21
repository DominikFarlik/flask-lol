from flask import Flask, render_template, request, redirect, url_for, jsonify
from functions import calculate_winrate, convert_epoch_to_duration
from api_functions import error, get_api_data, get_api_data_by_region, error_by_region
from db_functions import get_collection, update_new_players, sort_by_value

app = Flask(__name__)


# home page
@app.route('/')
def index():
    return render_template('index.html')


# displaying data(mostly for testing)
@app.route('/players', methods=['GET'])
def get_players():
    players = list(get_collection("challengers").find({}, {"_id": 0}))
    return jsonify(players), 200


# processing input from navbar input
@app.route('/processInput/navbar', methods=['POST', 'GET'])
def processInputNavbar():
    input_data = request.form['userInput']
    if input_data:
        return redirect(url_for('summoner', summoner_name=input_data))


# processing leaderboard update
@app.route('/processInput/leaderboardUpdate', methods=['POST', 'GET'])
def processInputLeaderboard():
    return redirect(url_for('leaderboard'))


# displaying data of specific summoner
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


# just list of current challengers with additional data
@app.route('/leaderboard', methods=['GET', 'POST'])
def leaderboard():
    if request.method == 'POST':
        # loading new data from api
        queue = "RANKED_SOLO_5x5"
        endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"

        if error(endpoint):
            return render_template('leaderboard.html', error=get_api_data(endpoint))

        api_data = get_api_data(endpoint)
        entries = api_data['entries']
        new_players_data = [{key: x[key] for key in ['summonerId', 'leaguePoints', 'wins', 'losses']} for x in entries]
        update_new_players(new_players_data)
        return redirect(url_for('leaderboard'))

    # local data from db
    data = sort_by_value('leaguePoints', "challengers")
    return render_template('leaderboard.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
