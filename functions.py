import time


def convert_epoch_to_duration(epoch):
    time_struct = time.localtime(epoch)
    if len(str(time_struct.tm_min)) == 1:
        minutes = "0" + str(time_struct.tm_min)
    else:
        minutes = str(time_struct.tm_min)

    if len(str(time_struct.tm_sec)) == 1:
        seconds = "0" + str(time_struct.tm_sec)
    else:
        seconds = str(time_struct.tm_sec)
    return minutes + ":" + seconds


def calculate_winrate(wins, losses):
    return round(wins / (wins + losses) * 100, 1)
