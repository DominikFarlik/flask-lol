from flask import Flask, render_template, request, redirect, url_for
from api_functions import handle_api_call
from db_functions import (save_leaderboard_data, sort_by_value, update_or_add_document_by_puuid,
                          get_summoner_data_by_puuid, split_and_save_ranked_data, add_queue_kda_spell_names_by_id,
                          get_puuid_by_name_and_tag, pick_role_and_sort, save_tierlist_data)

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
    gameName, tagLine = summoner_name.split(' #')
    errors = {}

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
            else:
                split_and_save_ranked_data(rank_data, puuid)

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
                    update_or_add_document_by_puuid({'match_history': match_history_data}, puuid, "summoner_collection")
                    add_queue_kda_spell_names_by_id(summoner_id)

    return redirect(url_for('summoner', summoner_name=summoner_name))


# displaying data of specific summoner
@app.route('/summoner/<summoner_name>', methods=['GET'])
def summoner(summoner_name):
    gameName, tagLine = summoner_name.split('#')
    errors = {}

    puuid = get_puuid_by_name_and_tag(gameName, tagLine)
    if not puuid:
        account_endpoint = f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
        account_data, account_error = handle_api_call(account_endpoint, "region")

        if account_error:
            errors['player_data_error'] = account_error
            return render_template('summoner.html', errors={})
        else:
            puuid = account_data['puuid']
            update_or_add_document_by_puuid(account_data, puuid, 'summoner_collection')

    data = get_summoner_data_by_puuid(puuid)
    match_history = data.get('match_history')
    if match_history:
        return render_template('summoner.html', data=data, errors={}, puuid=puuid)
    else:
        return redirect(url_for('update_summoner', summoner_name=gameName + " #" + tagLine))


# just list of current challengers with additional data
@app.route('/leaderboard', methods=['GET', 'POST'])
def leaderboard():
    # loading new data from api
    if request.method == 'POST':
        queue = "RANKED_SOLO_5x5"
        leaderboard_endpoint = f"/lol/league/v4/challengerleagues/by-queue/{queue}"
        api_data, error_message = handle_api_call(leaderboard_endpoint, "server")
        if api_data:
            save_leaderboard_data([{key: x[key] for key in ['summonerId', 'leaguePoints', 'wins', 'losses']} for x in
                                   api_data['entries']])
            return redirect(url_for('leaderboard'))

    # local data from db
    data = sort_by_value('leaguePoints', "challengers", -1)
    return render_template('leaderboard.html', data=data)


@app.route('/tierlist', methods=['GET', 'POST'])
def tierlist():
    # default values
    role = 'ALL'
    sort_order = 'winrate'
    direction = -1
    sort_tier = "CHALLENGER"

    if request.method == 'POST':
        if 'role' in request.form:
            role = request.form['role']

        if 'sort' in request.form:
            role = request.form['previous_role']
            sort_order = request.form['sort']
            if sort_order == request.form.get('previous_sort'):
                direction = 1

        if 'tier' in request.form:
            sort_tier = request.form['tier']

    queue = "RANKED_SOLO_5x5"
    tier = "DIAMOND"
    division = "I"
    leaderboard_endpoint = f"/lol/league-exp/v4/entries/{queue}/{tier}/{division}"
    api_data, error_message = handle_api_call(leaderboard_endpoint, "server")
    if error_message:
        return render_template('leaderboard.html', error=error_message)
    else:
        #save_tierlist_data(api_data)
        data = pick_role_and_sort(role, sort_order, direction, sort_tier)
    return render_template('tierlist.html', data=data, previous_role=role, previous_sort=sort_order)


if __name__ == '__main__':
    app.run(debug=True)
