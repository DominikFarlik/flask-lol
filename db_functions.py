import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from api_functions import get_puuid_by_id, get_name_and_tagline_by_puuid, get_matches, handle_api_call, \
    get_champion_from_json
from functions import calculate_winrate, convert_epoch_to_duration, convert_epoch_to_date

# mongoDB setup
uri = ("mongodb+srv://dominikfarlik:Vej.5.syp.yke@cluster0.elmflqy.mongodb.net/flask_lol?retryWrites=true&w=majority"
       "&appName=Cluster0")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["flask_lol"]
leaderboard_collection = db["leaderboard"]
summoner_collection = db["summoners"]
tierlist_players_collection = db["tierlist_players"]
tierlist_matches_collection = db["tierlist_matches"]
tierlist_final_collection = db["tierlist_final"]


def find_documents_without_element(collection, element):
    return collection.find(
        {'$or': [{element: {'$exists': False}}, {element: {"$exists": True, "$eq": None}}]})


def add_missing_puuids(collection):
    data_without_puuid = find_documents_without_element(collection, 'puuid')
    for document in data_without_puuid:
        puuid = get_puuid_by_id(document['summonerId'])
        if puuid is not None:
            collection.update_one({'summonerId': document['summonerId']},
                                  {"$set": {"puuid": puuid}})
        else:
            break


def add_missing_gameNames():
    data_without_gameNames = find_documents_without_element(leaderboard_collection, 'gameName')
    for document in data_without_gameNames:
        game_and_tag = get_name_and_tagline_by_puuid(document['puuid'])
        if game_and_tag:
            gameName = game_and_tag['gameName']
            tagLine = game_and_tag['tagLine']
            leaderboard_collection.update_one({'puuid': document['puuid']},
                                              {"$set": {"gameName": gameName, "tagLine": tagLine}})


def delete_old_documents(old_documents, new_documents, key, collection):
    new_summoner_ids = {player[key] for player in new_documents}
    players_to_remove = [player for player in old_documents if player[key] not in new_summoner_ids]
    if len(players_to_remove) > 0:
        for player in players_to_remove:
            query = {key: player[key]}
            collection.delete_one(query)


def sort_by_value(key, collection, direction):
    if collection == "challengers":
        return leaderboard_collection.find().sort(key, direction)
    if collection == "tierlist_final":
        return tierlist_final_collection.find().sort(key, direction)


# Updating db data or if they are not in db, they are added
def update_or_add_data_by_value(data, key, collection):
    for document in data:
        query = {key: document[key]}
        collection.update_one(query, {'$set': document}, upsert=True)


# Insert new document or update existing
def update_or_add_document_by_puuid(data, puuid, collection):
    if collection == "challengers_collection":
        collection = leaderboard_collection
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


def add_queue_kda_spell_names_by_id(summoner_id):
    player_data = summoner_collection.find_one({'id': summoner_id})

    summoner_names = {
        1: "SummonerBoost",
        3: "SummonerExhaust",
        4: "SummonerFlash",
        6: "SummonerHaste",
        7: "SummonerHeal",
        11: "SummonerSmite",
        12: "SummonerTeleport",
        14: "SummonerDot",
        32: "SummonerSnowball",
        2201: "SummonerCherryFlash",
        2202: "SummonerCherryHold",
    }

    queues = {
        400: "Normal Draft",
        420: "Ranked Solo",
        440: "Ranked Flex",
        450: "ARAM",
        700: "Clash",
        1020: "One For All",
        1700: "Arena",
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

    summoner_collection.update_one({'id': summoner_id},
                                   {'$set': {'match_history': player_data['match_history']}})


def get_puuid_by_name_and_tag(name, tag):
    player_data = summoner_collection.find_one(
        {'gameName': {"$regex": name, "$options": "i"}, 'tagLine': {"$regex": tag, "$options": "i"}})
    if player_data:
        return player_data['puuid']
    else:
        return None


def update_tierlist_element(data, query, value):
    if tierlist_players_collection.count_documents({value: {'$exists': True}}) == 0:
        for row in data:
            tierlist_players_collection.update_one({query: row[query]},
                                                   {'$set': {value: row[value]}}, upsert=True)


def add_players_match_ids():
    data_without_matches = tierlist_players_collection.find({'puuid': {'$exists': True},
                                                             '$or': [{'matches': {'$exists': False}},
                                                                     {'matches': {"$exists": True, "$eq": None}}]})
    for document in data_without_matches:
        tierlist_players_collection.update_one({'summonerId': document['summonerId']},
                                               {"$set": {"matches": get_matches(document['puuid'])}})


def add_matches_by_ids():
    given_player = {}
    opponent_player = {}
    team_position = ""
    keys_to_keep = ['win', 'championName']
    api_limit_exceeded = False

    for document in tierlist_players_collection.find():
        if api_limit_exceeded:
            break

        for match_id in document['matches']:
            match_endpoint = f"/lol/match/v5/matches/{match_id}"
            match_data, match_error = handle_api_call(match_endpoint, "region")

            if match_error:
                api_limit_exceeded = True
                print("Api limit exceeded")
                break

            else:
                for participant in match_data['info']['participants']:
                    if participant['summonerId'] == document['summonerId']:
                        given_player = {key: participant[key] for key in keys_to_keep}
                        team_position = participant['teamPosition']
                        break

                if (tierlist_matches_collection.find_one({'matchId': match_id, 'teamPosition': team_position}) is None
                        and given_player != {}):
                    for participant in match_data['info']['participants']:
                        if participant['teamPosition'] == team_position and participant['win'] != given_player['win']:
                            opponent_player = {key: participant[key] for key in keys_to_keep}
                            break

                    if team_position != '':
                        if tierlist_matches_collection.find_one(
                                {'matchId': match_id, 'teamPosition': team_position}) is None:
                            tierlist_matches_collection.insert_one({'matchId': match_id,
                                                                    'teamPosition': team_position,
                                                                    'tier': document['tier'],
                                                                    'player1': given_player,
                                                                    'player2': opponent_player})
        tierlist_players_collection.delete_one({'summonerId': document['summonerId']})


def combine_tierlist_data_winrates():
    # Get all unique champion names
    unique_champions = set()
    cursor = tierlist_matches_collection.find({}, {"player1.championName": 1, "player2.championName": 1})
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
        for role in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']:
            # Count total games played with the champion in the role
            total_games = tierlist_matches_collection.count_documents({
                "$or": [{"player1.championName": champion_name, "teamPosition": role},
                        {"player2.championName": champion_name, "teamPosition": role}]})
            # Count wins with the champion in the role
            wins = tierlist_matches_collection.count_documents(
                {"$or": [{"player1.championName": champion_name, "player1.win": True, "teamPosition": role},
                         {"player2.championName": champion_name, "player2.win": True, "teamPosition": role}]})

            if total_games >= 1:
                win_rate = (wins / total_games) * 100

                # this champion just have bad name format for api
                if champion_name == "FiddleSticks":
                    champion_name = "Fiddlesticks"
                # Save win rate for champion-role combination
                tierlist_final_collection.update_one({'championImg': champion_name},
                                                     {'$set': {
                                                         'championName': get_champion_from_json(champion_name),
                                                         'championImg': champion_name,
                                                         'role': role,
                                                         'winrate': round(win_rate, 2),
                                                         'matches': total_games}},
                                                     upsert=True)


def add_pickrate_and_tier():
    matches = list(tierlist_matches_collection.aggregate([{"$group": {"_id": "$matchId", "count": {"$sum": 1}}}]))
    low_pickrate = tierlist_final_collection.count_documents({"matches": {"$lt": 6}})

    match_count = len(matches) - low_pickrate

    for champion in tierlist_final_collection.find({}):
        champion['pickrate'] = round((champion['matches'] / match_count) * 100 * 5, 2)
        champion['champion_tier'] = round(((champion['pickrate'] * 0.1) * (champion['winrate'])) / 10, 1)
        tierlist_final_collection.update_one({'role': champion['role'], 'championName': champion['championName']},
                                             {'$set': champion})


def pick_role_and_sort(role, key, direction, tier):
    sorted_data = sort_by_value(key, "tierlist_final", direction)
    if role != 'ALL':
        return [doc for doc in sorted_data if doc.get('role') == role and doc.get('matches') > 5]
    else:
        return [doc for doc in sorted_data if doc.get('matches') > 5]


def save_tierlist_data(data):
    print("Setting summonerIds")
    update_tierlist_element(data, 'summonerId', 'summonerId')
    print("Setting player tiers")
    update_tierlist_element(data, 'summonerId', 'tier')
    print("Fetching puuids")
    add_missing_puuids(tierlist_players_collection)
    print("Fetching match Ids")
    add_players_match_ids()
    print("Fetching match data")
    add_matches_by_ids()
    print("Calculating win rates")
    combine_tierlist_data_winrates()
    print("Calculating pick rates")
    add_pickrate_and_tier()


def save_leaderboard_data(new_players):
    delete_old_documents(leaderboard_collection.find(), new_players, 'summonerId', leaderboard_collection)
    update_or_add_data_by_value(new_players, 'summonerId', leaderboard_collection)
    add_or_update_winrate_for_collection(leaderboard_collection)
    add_missing_puuids(leaderboard_collection)
    add_missing_gameNames()
