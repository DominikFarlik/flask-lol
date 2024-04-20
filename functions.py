import time


def calculate_winrate(data):
    winrate = round((data['wins'] / (data['wins'] + data['losses'])) * 100, 1)
    return winrate


def convert_epoch_to_duration(epoch):
    time_struct = time.localtime(epoch)
    return str(time_struct.tm_min) + ":" + str(time_struct.tm_sec)
