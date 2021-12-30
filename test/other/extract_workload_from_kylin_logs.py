import os
from collections import Counter
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd


def process_logfile(log_file) -> list:
    with open(log_file, mode='r', encoding='utf-8') as file:
        lines = file.readlines()
    return [line.split(" : ")[0] for line in lines]


if __name__ == '__main__':
    # extract datetime strings from log files
    query_timestamps = []

    # logs_dir = os.path.join(os.environ['RAVEN_HOME'], 'resources', 'sql_logs-customer4', '4', 'logs')
    logs_dir = os.path.join(os.environ['RAVEN_HOME'], 'resources', 'sql_logs-customer1-3')
    for filename in os.listdir(logs_dir):
        query_timestamps += process_logfile(os.path.join(logs_dir, filename))
    # print(query_timestamps)

    conv_time = [datetime.strptime(_, '%Y-%m-%d %H:%M:%S') for _ in query_timestamps]

    query_timestamps = [dt.strftime('%Y-%m-%d %H:%M:%S') for dt in conv_time]
    query_timestamps.sort()
    for t in query_timestamps:
        print(t)
    # print(query_timestamps)

    # mylist = dict(Counter(query_timestamps)).items()
    # dt = [datetime.strptime(t[0], '%Y-%m-%d %H:%M') for t in mylist]
    # qps = [t[1] / 60.0 for t in mylist]
    # df = pd.DataFrame({'qps': qps}, index=pd.DatetimeIndex(dt))
    # df['qps'].plot(xlabel='time', ylabel='QPS')
    # plt.ylim(0, 2.0)
    # plt.show()

    # # convert strings into datetime objects
    # conv_time = [datetime.strptime(_, '%Y-%m-%d %H:%M:%S') for _ in query_timestamps]
    # # print(conv_time)
    #
    # # define bin number
    # bin_nr = 150
    # fig, ax = plt.subplots(1, 1)
    #
    # # create histogram, get bin position for label
    # _counts, bins, _patches = ax.hist(conv_time, bins=bin_nr)
    #
    # # set xticks at bin edges
    # plt.xticks(bins)
    #
    # # reformat bin label into format hour:minute
    # # ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    #
    # plt.show()
