import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from api_functions import get_puuid_by_id, get_name_and_tagline_by_puuid
from functions import calculate_winrate

# mongoDB setup
uri = ("mongodb+srv://dominikfarlik:Vej.5.syp.yke@cluster0.elmflqy.mongodb.net/flask_lol?retryWrites=true&w=majority"
       "&appName=Cluster0")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["flask_lol"]
players_collection = db["players"]


def find_documents_without_element(element):
    return players_collection.find(
        {'$or': [{element: {'$exists': False}}, {element: {"$exists": True, "$eq": None}}]})


def add_missing_puuids():
    data_without_puuid = find_documents_without_element('puuid')
    for document in data_without_puuid:
        players_collection.update_one({'summonerId': document['summonerId']},
                                      {"$set": {"puuid": get_puuid_by_id(document['summonerId'])}})


def add_missing_gameNames():
    #data_without_gameNames = find_documents_without_element('gameName')
    data_without_gameNames = find_documents_without_element('tagLine')
    for document in data_without_gameNames:
        game_and_tag = get_name_and_tagline_by_puuid(document['puuid'])
        if game_and_tag:
            gameName = game_and_tag['gameName']
            tagLine = game_and_tag['tagLine']
        else:
            gameName = None
            tagLine = None
        players_collection.update_one({'puuid': document['puuid']},
                                      {"$set": {"gameName": gameName, "tagLine": tagLine}})


def update_new_players(new_players):
    # data prepare for update
    old_players = players_collection.find()
    new_summoner_ids = {player['summonerId'] for player in new_players}
    players_to_remove = [player for player in old_players if player['summonerId'] not in new_summoner_ids]
    if len(players_to_remove) > 0:
        # removing old players, that does not match new
        for player in players_to_remove:
            query = {'summonerId': player['summonerId']}
            players_collection.delete_one(query)
        print("Old player data removed")

    # updating all players data, if they are not in db, they are added
    for player in new_players:
        player['winrate'] = calculate_winrate(player)
        query = {'summonerId': player['summonerId']}
        players_collection.update_one(query, {'$set': player}, upsert=True)
    print("Players updated")
    add_missing_puuids()
    print("Player puuids added")
    add_missing_gameNames()
    print("Player names added")


def get_collection(collection):
    if collection == "players":
        return players_collection


def sort_by_value(key, collection):
    if collection == "players":
        return players_collection.find().sort(key, pymongo.ASCENDING)
