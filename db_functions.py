import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from api_functions import get_puuid_by_id, get_name_and_tagline_by_puuid, get_matches, handle_api_call
from functions import calculate_winrate, convert_epoch_to_duration, convert_epoch_to_date

# mongoDB setup
uri = ("mongodb+srv://dominikfarlik:Vej.5.syp.yke@cluster0.elmflqy.mongodb.net/flask_lol?retryWrites=true&w=majority"
       "&appName=Cluster0")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["flask_lol"]
challenger_collection = db["challengers"]
summoner_collection = db["summoners"]
tierlist_collection = db["champion_stats"]
matches_collection = db["matches"]


def find_documents_without_element(collection, element):
    return collection.find(
        {'$or': [{element: {'$exists': False}}, {element: {"$exists": True, "$eq": None}}]})


def add_missing_puuids(collection):
    if collection == "challenger_collection":
        collection = challenger_collection
    elif collection == "tierlist_collection":
        collection = tierlist_collection
    data_without_puuid = find_documents_without_element(collection, 'puuid')
    for document in data_without_puuid:
        collection.update_one({'summonerId': document['summonerId']},
                              {"$set": {"puuid": get_puuid_by_id(document['summonerId'])}})


def add_missing_gameNames():
    data_without_gameNames = find_documents_without_element('gameName')
    for document in data_without_gameNames:
        game_and_tag = get_name_and_tagline_by_puuid(document['puuid'])
        if game_and_tag:
            gameName = game_and_tag['gameName']
            tagLine = game_and_tag['tagLine']
        else:
            gameName = None
            tagLine = None
        challenger_collection.update_one({'puuid': document['puuid']},
                                         {"$set": {"gameName": gameName, "tagLine": tagLine}})


def update_new_players(new_players):
    delete_old_documents(challenger_collection.find(), new_players, 'summonerId', challenger_collection)
    update_or_add_data_by_value(new_players, 'summonerId', challenger_collection)
    add_or_update_winrate_for_collection(challenger_collection)
    add_missing_puuids("tierlist_collection")
    add_missing_gameNames()


def delete_old_documents(old_documents, new_documents, key, collection):
    new_summoner_ids = {player[key] for player in new_documents}
    players_to_remove = [player for player in old_documents if player[key] not in new_summoner_ids]
    if len(players_to_remove) > 0:
        # removing old players, that do not match new
        for player in players_to_remove:
            query = {key: player[key]}
            collection.delete_one(query)


def get_collection(collection):
    if collection == "challengers":
        return challenger_collection
    if collection == "summoners":
        return summoner_collection


def sort_by_value(key, collection):
    if collection == "challengers":
        return challenger_collection.find().sort(key, pymongo.DESCENDING)


# Updating db data or if they are not in db, they are added
def update_or_add_data_by_value(data, key, collection):
    for document in data:
        query = {key: document[key]}
        collection.update_one(query, {'$set': document}, upsert=True)


# Insert new document or update existing
def update_or_add_document_by_puuid(data, puuid, collection):
    if collection == "challengers_collection":
        collection = challenger_collection
    elif collection == "summoner_collection":
        collection = summoner_collection
    query = {'puuid': puuid}
    collection.update_one(query, {'$set': data}, upsert=True)


# adding winrate value, to given collection
def add_or_update_winrate_for_collection(collection):
    for document in collection.find():
        query = {'summonerId': document['summonerId']}
        winrate = calculate_winrate(document['wins'], document['losses'])
        collection.update_one(query, {'$set': {'winrate': winrate}}, upsert=True)


def get_summoner_data_by_puuid(puuid):
    return summoner_collection.find_one({'puuid': puuid})


def split_and_save_ranked_data(data, puuid):
    for queue in data:
        if queue['queueType'] == 'RANKED_SOLO_5x5':
            queue['winrate'] = calculate_winrate(queue['wins'], queue['losses'])
            update_or_add_document_by_puuid({'ranked_solo': queue}, puuid, summoner_collection)

        elif queue['queueType'] == 'RANKED_FLEX_SR':
            queue['winrate'] = calculate_winrate(queue['wins'], queue['losses'])
            update_or_add_document_by_puuid({'ranked_flex': queue}, puuid, summoner_collection)


def add_summoner_spell_names(summoner_id):
    player_data = summoner_collection.find_one({'id': summoner_id})

    summoner_names = {
        1: "SummonerBoost",
        3: "SummonerExhaust",
        4: "SummonerFlash",
        6: "SummonerHaste",
        7: "SummonerHeal",
        11: "SummonerSmite",
        12: "SummonerTeleport",
        14: "SummonerDot"
    }

    queues = {
        400: "Normal Draft",
        420: "Ranked Solo",
        440: "Ranked Flex",
        450: "ARAM",
        700: "Clash",
        1020: "One For All",
        1900: "URF",
    }

    for match_data in player_data.get('match_history', []):

        match_data['info']['gameEndTimestamp'] = convert_epoch_to_date(match_data['info']['gameEndTimestamp'])
        match_data['info']['gameDuration'] = convert_epoch_to_duration(match_data['info']['gameDuration'])
        match_data['info']['queueName'] = queues[match_data['info']['queueId']]

        for match in match_data['info']['participants']:
            summoner1_id = match.get('summoner1Id')
            if summoner1_id in summoner_names:
                match['summoner1Name'] = summoner_names[summoner1_id]

            summoner2_id = match.get('summoner2Id')
            if summoner2_id in summoner_names:
                match['summoner2Name'] = summoner_names[summoner2_id]

            if match['deaths'] != 0:
                match['kda'] = "{:.2f}".format(
                    (match['kills'] + match['assists']) / match['deaths'])
            else:
                match['kda'] = "{:.2f}".format((match['kills'] + match['assists']) / 1)

    summoner_collection.update_one(
        {'id': summoner_id},
        {'$set': {'match_history': player_data['match_history']}}
    )


def get_puuid_by_name_and_tag(name, tag):
    player_data = summoner_collection.find_one(
        {'gameName': {"$regex": name, "$options": "i"}, 'tagLine': {"$regex": tag, "$options": "i"}})
    if player_data:
        return player_data['puuid']
    else:
        return None


def update_tierlist_element(data, element, value):
    for row in data:
        tierlist_collection.update_one(
            {element: row[element]},
            {'$set': {value: row[value]}}, upsert=True)


def add_players_match_ids():
    data_without_matches = find_documents_without_element(tierlist_collection, 'matches')
    for document in data_without_matches:
        tierlist_collection.update_one({'summonerId': document['summonerId']},
                                       {"$set": {"matches": get_matches(document['puuid'])}})


def add_matches_by_ids():
    given_player = {}
    opponent_player = {}
    team_position = ""
    keys_to_keep = ['win', 'championName']
    api_limit_exceeded = False

    for document in tierlist_collection.find():
        for match_id in document['matches']:
            if matches_collection.find_one({'matchId': match_id}) is None:
                print("adding match")
                match_endpoint = f"/lol/match/v5/matches/{match_id}"
                match_data, match_error = handle_api_call(match_endpoint, "region")

                if match_error:
                    api_limit_exceeded = True
                    break
                else:
                    for participant in match_data['info']['participants']:
                        if participant['summonerId'] == document['summonerId']:
                            given_player = {key: participant[key] for key in keys_to_keep}
                            team_position = participant['teamPosition']
                            break

                    for participant in match_data['info']['participants']:
                        if participant['teamPosition'] == team_position and participant['win'] != given_player['win']:
                            opponent_player = {key: participant[key] for key in keys_to_keep}
                            break

                    if team_position != '':
                        if matches_collection.find_one({'matchId': match_id, 'teamPosition': team_position}) is None:
                            matches_collection.insert_one({'matchId': match_id,
                                                           'teamPosition': team_position,
                                                           'tier': document['tier'],
                                                           'player1': given_player,
                                                           'player2': opponent_player})
        if api_limit_exceeded:
            break


def calculate_winrate_of_champion():
    # Get all unique champion names
    unique_champions = set()
    cursor = matches_collection.find({}, {"player1.championName": 1, "player2.championName": 1})
    for document in cursor:
        unique_champions.add(document["player1"]["championName"])
        unique_champions.add(document["player2"]["championName"])

    # Initialize dictionary to store win rates by champion-role
    champion_winrates = {}

    # Iterate over champion names
    for champion_name in unique_champions:
        # Initialize dictionary to store win rates by role
        champion_winrates[champion_name] = {}

        # Iterate over roles
        for role in ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]:
            # Count total games played with the champion in the role
            total_games = matches_collection.count_documents({
                "$or": [
                    {"player1.championName": champion_name, "teamPosition": role},
                    {"player2.championName": champion_name, "teamPosition": role}
                ]
            })

            # Count wins with the champion in the role
            wins = matches_collection.count_documents({
                "$or": [
                    {"player1.championName": champion_name, "player1.win": True, "teamPosition": role},
                    {"player2.championName": champion_name, "player2.win": True, "teamPosition": role}
                ]
            })

            # Calculate win rate
            if total_games >= 10:  # Only consider roles with 10 or more games
                if total_games > 0:
                    win_rate = (wins / total_games) * 100
                else:
                    win_rate = 0

                # Save win rate for champion-role combination
                champion_winrates[champion_name][role] = {'winrate': win_rate, 'matches': total_games}

    return champion_winrates
