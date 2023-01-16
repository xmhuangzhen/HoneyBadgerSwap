import re
import sys

import numpy

idx_seq = 2
idx_op = 4
idx_time = 6

names = [
    'mpc_extension',
    'zkrp',
    'mpc',
]

idx_start = [
    '1',
    '2',
    '3',
]

idx_end = [
    '5',
    '3',
    '4',
]

def scan(path, prog, serverID):
    total_time = numpy.zeros(len(names))
    total_cnt = numpy.zeros(len(names))

    file = f'./{path}/latency_{prog}_{serverID}.csv'
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            element = re.split('\t|\n', line)

            op = element[idx_op]
            time = float(element[idx_time])

            for i, (start, end) in enumerate(zip(idx_start, idx_end)):
                if op == start:
                    total_time[i] -= time
                    total_cnt[i] += 1
                if op == end:
                    total_time[i] += time

    # print(serverID)
    # for name, time, cnt in zip(names, total_time, total_cnt):
    #     print(name, time / cnt)
    print(tuple([time / cnt for time, cnt in zip(total_time, total_cnt)]))
    return tuple([time / cnt for time, cnt in zip(total_time, total_cnt)])


if __name__ == '__main__':
    players = int(sys.argv[1])
    path = sys.argv[2]
    prog = sys.argv[3]

    times = numpy.zeros(len(names))

    for serverID in range(players):
        times += scan(path, prog, serverID)

    times /= players

    db_time = times[0]-numpy.sum(times[1:])

    print('===========')
    for name, time in zip(names, times):
        print(name, time)
    print('db', db_time)

