import time

from db_functions import update_or_add_document_by_id


def convert_epoch_to_duration(epoch):
    time_struct = time.localtime(epoch)
    return str(time_struct.tm_min) + ":" + str(time_struct.tm_sec)


def split_and_save_ranked_data(data):
    for queue in data:
        if queue['queueType'] == 'RANKED_SOLO_5x5':
            queue['winrate'] = calculate_winrate(queue['wins'], queue['losses'])
            update_or_add_document_by_id({'ranked_solo': queue, 'id': queue['summonerId']},
                                         'summoner_collection')

        elif queue['queueType'] == 'RANKED_FLEX_SR':
            queue['winrate'] = calculate_winrate(queue['wins'], queue['losses'])
            update_or_add_document_by_id({'ranked_flex': queue, 'id': queue['summonerId']},
                                         'summoner_collection')


def calculate_winrate(wins, losses):
    return round(wins / (wins + losses) * 100, 1)
