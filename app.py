from flask import Flask, render_template, request, redirect, url_for
from functions import convert_epoch_to_duration
from api_functions import handle_api_call
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
    summoner_name = request.form['summoner_name']
    if '#' not in summoner_name:
        summoner_name = summoner_name + " #EUNE"
    return redirect(url_for('summoner', summoner_name=summoner_name))


@app.route('/summoner/<summoner_name>/updated', methods=['POST', 'GET'])
def update_summoner(summoner_name):
    print("entered summoner update func")
    gameName, tagLine = summoner_name.split(' #')
    errors = {}
    puuid = ""

    # getting puuid
    account_endpoint = f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    account_data, account_error = handle_api_call(account_endpoint, "region")
    if account_error:
        errors['player_data_error'] = account_error
    else:
        puuid = account_data['puuid']
        update_or_add_document_by_puuid(account_data, puuid, 'summoner_collection')

        # getting summoner_id level and icon
        summoner_endpoint = f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        summoner_data, summoner_error = handle_api_call(summoner_endpoint, "server")
        if summoner_error:
            errors['player_data_error'] = summoner_error
        else:
            summoner_data['gameName'] = gameName
            summoner_id = summoner_data['id']
            update_or_add_document_by_puuid(summoner_data, puuid, 'summoner_collection')

            # getting information about player rank statistics
            rank_endpoint = f"/lol/league/v4/entries/by-summoner/{summoner_id}"
            rank_data, rank_error = handle_api_call(rank_endpoint, "server")
            if rank_error:
                errors['rank_error'] = rank_error
                print("rank error")
            else:
                split_and_save_ranked_data(rank_data, puuid)
                print("rank updated")

            # Retrieve match ids
            match_history_endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
            match_history_ids, match_history_error = handle_api_call(match_history_endpoint, "region")
            if match_history_error:
                errors['match_history_error'] = match_history_error
            else:
                # Retrieve match data by ids
                match_history_data = []
                for match_id in match_history_ids:
                    match_endpoint = f"/lol/match/v5/matches/{match_id}"
                    match_data, match_error = handle_api_call(match_endpoint, "region")
                    if not match_error:
                        match_history_data.append(match_data)
                # processing match data
                if not match_history_data:
                    errors['match_history_error'] = "Matches not found"
                else:
                    match_history = [participant for match in match_history_data for participant in
                                     match['info']['participants'] if participant['summonerId'] == summoner_id]
                    update_or_add_document_by_puuid({'match_history': match_history}, puuid,
                                                    "summoner_collection")
                    print("match history updated")
                    add_summoner_spell_names(summoner_id)
                    add_kda(summoner_id)

    return redirect(url_for('summoner', summoner_name=summoner_name))


# displaying data of specific summoner
@app.route('/summoner/<summoner_name>', methods=['GET'])
def summoner(summoner_name):
    print("entered summoner function")
    gameName, tagLine = summoner_name.split(' #')
    errors = {}

    account_endpoint = f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    account_data, account_error = handle_api_call(account_endpoint, "region")

    if account_error:
        errors['player_data_error'] = account_error
    elif account_data:
        puuid = account_data['puuid']
        update_or_add_document_by_puuid(account_data, puuid, 'summoner_collection')

        data = get_summoner_data_by_puuid(puuid)
        match_history = data.get('match_history')
        if match_history:
            return render_template('summoner.html', data=data, errors={})
        else:
            return redirect(url_for('update_summoner', summoner_name=gameName + " #" + tagLine))


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
        leaderboard_endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"
        api_data, error_message = handle_api_call(leaderboard_endpoint, "server")
        if error_message:
            return render_template('leaderboard.html', error=error_message)
        else:
            entries = api_data['entries']
            new_players_data = [{key: x[key] for key in ['summonerId', 'leaguePoints', 'wins', 'losses']} for x in
                                entries]
            update_new_players(new_players_data)
            return redirect(url_for('leaderboard'))

    # local data from db
    data = sort_by_value('leaguePoints', "challengers")
    return render_template('leaderboard.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
