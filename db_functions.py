import pymongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from api_functions import get_puuid_by_id, get_name_and_tagline_by_puuid

# mongoDB setup
uri = ("mongodb+srv://dominikfarlik:Vej.5.syp.yke@cluster0.elmflqy.mongodb.net/flask_lol?retryWrites=true&w=majority"
       "&appName=Cluster0")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["flask_lol"]
challenger_collection = db["challengers"]
summoner_collection = db["summoners"]


def find_documents_without_element(element):
    return challenger_collection.find(
        {'$or': [{element: {'$exists': False}}, {element: {"$exists": True, "$eq": None}}]})


def add_missing_puuids():
    data_without_puuid = find_documents_without_element('puuid')
    for document in data_without_puuid:
        challenger_collection.update_one({'summonerId': document['summonerId']},
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
    delete_old_documents(challenger_collection.find(), new_players)
    update_or_add_data_by_value(new_players, 'summonerId', challenger_collection)
    add_or_update_winrate(challenger_collection)
    add_missing_puuids()
    add_missing_gameNames()


def delete_old_documents(old_documents, new_documents):
    new_summoner_ids = {player['summonerId'] for player in new_documents}
    players_to_remove = [player for player in old_documents if player['summonerId'] not in new_summoner_ids]
    if len(players_to_remove) > 0:
        # removing old players, that do not match new
        for player in players_to_remove:
            query = {'summonerId': player['summonerId']}
            challenger_collection.delete_one(query)


def get_collection(collection):
    if collection == "challengers":
        return challenger_collection
    if collection == "summoners":
        return summoner_collection


def sort_by_value(key, collection):
    if collection == "challengers":
        return challenger_collection.find().sort(key, pymongo.ASCENDING)


# Updating db data or if they are not in db, they are added
def update_or_add_data_by_value(data, key, collection):
    for document in data:
        query = {key: document[key]}
        collection.update_one(query, {'$set': document}, upsert=True)


# Insert new document or update existing
def update_or_add_document_by_id(data, collection):
    if collection == "summoner_collection":
        collection = summoner_collection
    query = {'id': data['id']}
    collection.update_one(query, {'$set': data}, upsert=True)


# adding winrate value, to given collection
def add_or_update_winrate(collection):
    pipeline = [
        # Calculate winrate and insert it into collection
        {'$addFields': {
            'winrate': {'$round': [{'$multiply': [{'$divide': ['$wins', {'$sum': ['$wins', '$losses']}]}, 100]}, 1]}}
        },
        # Update the 'winrate' field with the newly calculated value, if there was existing
        {'$set': {'winrate': '$winrate'}
         }
    ]
    collection.aggregate(pipeline)


def get_summoner_data_by_id(summoner_id):
    return summoner_collection.find_one({'id': summoner_id})
