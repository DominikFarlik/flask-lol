from flask import Flask, render_template, request, redirect, url_for, jsonify
from functions import convert_epoch_to_duration
from api_functions import error, get_api_data, get_api_data_by_region, error_by_region
from db_functions import (update_new_players, sort_by_value, update_or_add_document_by_puuid,
                          get_summoner_data_by_puuid, split_and_save_ranked_data, add_summoner_spell_names, add_kda)

app = Flask(__name__)


# home page
@app.route('/')
def index():
    return render_template('index.html')


# processing input from navbar input
@app.route('/processInput/navbar', methods=['POST', 'GET'])
def processInputNavbar():
    summoner_name = request.form['userInput']
    if '#' not in summoner_name:
        summoner_name = summoner_name + " #EUNE"
    return redirect(url_for('summoner', summoner_name=summoner_name))


# displaying data of specific summoner
@app.route('/summoner/<summoner_name>')
def summoner(summoner_name):
    errors = {}
    gameName, tagLine = summoner_name.split(' #')

    endpoint = f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    if error_by_region(endpoint):
        errors['player_data_error'] = get_api_data_by_region(endpoint)
    else:
        api_data = get_api_data_by_region(endpoint)
        print(api_data)
        encryptedPUUID = api_data['puuid']
        update_or_add_document_by_puuid(api_data, encryptedPUUID, 'summoner_collection')
        data = get_summoner_data_by_puuid(encryptedPUUID)
        match_history = data.get('match_history')
        if match_history:
            return render_template('summoner.html', data=data, errors={})
        #else:
            #return redirect(url_for('summonerUpdate', gameName=gameName, tagLine=tagLine))


@app.route('/summoner/updated', methods=['POST', 'GET'])
def summonerUpdate():
    gameName = request.form['gameName']
    tagLine = request.form['tagLine']
    errors = {}
    match_history_data = []
    print(gameName, tagLine)

    endpoint = f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    if error_by_region(endpoint):
        errors['player_data_error'] = get_api_data_by_region(endpoint)
    else:
        api_data = get_api_data_by_region(endpoint)
        print(api_data)
        encryptedPUUID = api_data['puuid']

        # getting summoner level and icon
        endpoint = f"/lol/summoner/v4/summoners/by-puuid/{encryptedPUUID}"
        if error(endpoint):
            errors['player_data_error'] = get_api_data(endpoint)
            pass
        else:
            api_data = get_api_data(endpoint)
            print(api_data)
            api_data['gameName'] = gameName

            summoner_id = api_data['id']
            update_or_add_document_by_puuid(api_data, encryptedPUUID, 'summoner_collection')

        # getting information about player rank statistics
        endpoint = f"/lol/league/v4/entries/by-summoner/{api_data['id']}"
        if error(endpoint):
            errors['rank_error'] = get_api_data(endpoint)
            pass
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
                # pick data to store for current summoner
                for i in match_history_data:
                    for j in i['info']['participants']:
                        if j['summonerId'] == summoner_id:
                            match_history.append(j)
                update_or_add_document_by_puuid({'match_history': match_history}, encryptedPUUID, "summoner_collection")
                add_summoner_spell_names(summoner_id)
                add_kda(summoner_id)

    return redirect(url_for('summoner', summoner_name=gameName + " #" + tagLine))


# processing leaderboard update
@app.route('/processInput/leaderboardUpdate', methods=['POST', 'GET'])
def processInputLeaderboard():
    return redirect(url_for('leaderboard'))


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
