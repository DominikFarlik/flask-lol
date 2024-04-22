import time


def convert_epoch_to_duration(epoch):
    time_struct = time.localtime(epoch)
    return str(time_struct.tm_min) + ":" + str(time_struct.tm_sec)


def calculate_winrate(wins, losses):
    return round(wins / (wins + losses) * 100, 1)
