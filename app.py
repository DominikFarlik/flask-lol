from flask import Flask, render_template, request, redirect, url_for, jsonify
from functions import convert_epoch_to_duration
from api_functions import error, get_api_data, get_api_data_by_region, error_by_region
from db_functions import (get_collection, update_new_players, sort_by_value, update_or_add_document_by_id,
                          get_summoner_data_by_id, split_and_save_ranked_data, change_summ_spell_id_to_name)

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
    errors = {}
    match_history_data = []
    #change_summ_spell_id_to_name('ux5iNhCX9pHOyOepp4914QwEq_iIJ2tioPhKGiDNhkWPKe0')
    # getting summoner level and icon
    #endpoint = f"/lol/summoner/v4/summoners/by-name/{summoner_name}"
    #if error(endpoint):
    #    return render_template('summoner.html', player_data_error=get_api_data(endpoint))
    #else:
    #    api_data = get_api_data(endpoint)
    #    api_data['gameName'] = summoner_name
    #    summoner_id = api_data['id']
        #update_or_add_document_by_id(api_data, summoner_id, 'summoner_collection')
        #if request.method == 'POST':
        #    # Run the code you provided for POST request
        #    data = get_summoner_data_by_id(summoner_id)
        #    return render_template('summoner.html', data=data, errors=errors)
    data = get_summoner_data_by_id('ux5iNhCX9pHOyOepp4914QwEq_iIJ2tioPhKGiDNhkWPKe0')
    return render_template('summoner.html', data=data, errors=errors)
    # getting information about player rank statistics
    endpoint = f"/lol/league/v4/entries/by-summoner/{api_data['id']}"
    if error(endpoint):
        errors['rank_error'] = get_api_data(endpoint)
    else:
        split_and_save_ranked_data(get_api_data(endpoint))

    # getting player matches
    endpoint = f"/lol/match/v5/matches/by-puuid/{api_data['puuid']}/ids"
    if error_by_region(endpoint):
        errors['match_history_error'] = get_api_data_by_region(endpoint)
    else:
        data = get_api_data_by_region(endpoint)

        # processing match data
        for matchId in data:
            match_history_data.append(get_api_data_by_region(f"/lol/match/v5/matches/{matchId}"))

        match_history = []
        # pick data to store
        for i in match_history_data:
            for j in i['info']['participants']:
                if j['summonerId'] == summoner_id:
                    match_history.append(j)
        update_or_add_document_by_id({'match_history': match_history}, summoner_id, "summoner_collection")

    data = get_summoner_data_by_id(summoner_id)
    return render_template('summoner.html', data=data, errors=errors)


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
