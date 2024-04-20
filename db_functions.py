from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from api_functions import get_puuid_by_id

# mongoDB setup
uri = ("mongodb+srv://dominikfarlik:Vej.5.syp.yke@cluster0.elmflqy.mongodb.net/flask_lol?retryWrites=true&w=majority"
       "&appName=Cluster0")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["flask_lol"]
players_collection = db["players"]


def find_document_without_puuid():
    return players_collection.find(
        {'$or': [{"puuid": {'$exists': False}}, {"puuid": {"$exists": True, "$eq": None}}]})


def add_missing_puuids(data_without_puuid):
    for document in data_without_puuid:
        players_collection.update_one({'summonerId': document['summonerId']},
                                      {"$set": {"puuid": get_puuid_by_id(document['summonerId'])}})


def update_new_players(new_players):
    # data prepare for update
    old_players = players_collection.find()
    new_summoner_ids = {player['summonerId'] for player in new_players}
    players_to_remove = [player for player in old_players if player['summonerId'] not in new_summoner_ids]

    # removing old players, that does not match new
    for player in players_to_remove:
        query = {'summonerId': player['summonerId']}
        players_collection.delete_one(query)

    # updating all players data, if they are not in db, they are added
    for player in new_players:
        query = {'summonerId': player['summonerId']}
        players_collection.update_one(query, {'$set': player}, upsert=True)


def get_collection(collection):
    if collection == "players":
        return players_collection
