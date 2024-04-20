from flask import Flask, render_template, request, redirect, url_for, jsonify
from functions import error, get_api_data, get_api_data_by_region, calculate_winrate, get_name_by_puuid, get_puuid_by_id, \
    load_puuids_to_file_from_ids, error_by_region
import time
import pprint
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = Flask(__name__)

# mongoDB setup
uri = ("mongodb+srv://dominikfarlik:Vej.5.syp.yke@cluster0.elmflqy.mongodb.net/flask_lol?retryWrites=true&w=majority"
       "&appName=Cluster0")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["flask_lol"]
players_collection = db["players"]

# verifying connection with db
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/players', methods=['GET'])
def get_users():
    pprint.pprint(players_collection.find({}))
    players = players_collection.find_one()
    return players['name'], 200


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
            time_struct = time.localtime(i['info']['gameDuration'])
            i['info']['gameDuration'] = str(time_struct.tm_min) + ":" + str(time_struct.tm_sec)
    print(match_history_data[0])

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
        data = get_api_data(endpoint)
        data = data['entries']
        summIds = [{key: d[key] for key in ['summonerId', 'leaguePoints', 'wins', 'losses']} for d in data]
        players_collection.insert_many(summIds)

        # load_puuids_to_file_from_ids(data)
        data = sorted(data, key=lambda x: -x['leaguePoints'])
        return render_template('challenger.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)
