import re
import sys

import numpy

idx_op = 1
idx_time = 3

names = [
    'overall',
    'collect_keys',
    'gen_state_mask',
    'consume_state_mask',
    'send_request',
    'interpolate',
    'restore_db',
]

idx_start = [
    2,
    1,
    2,
    3,
    4,
    5,
    6,
]

idx_end = [
    7,
    2,
    3,
    4,
    5,
    6,
    7,
]

if __name__ == '__main__':
    repetition = int(sys.argv[1])
    rep = int(sys.argv[2])

    times = numpy.zeros(len(names))

    file = f'ratel/benchmark/data/recover_states_{repetition}.csv'
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            element = re.split('\t|\n', line)

            op = int(element[idx_op])
            time = float(element[idx_time])
            # print(op, time)

            for i, (start, end) in enumerate(zip(idx_start, idx_end)):
                if op == start:
                    times[i] -= time
                if op == end:
                    times[i] += time

    str_names = ''
    str_times = ''
    for name, time in zip(names, times):
        str_names += f'{name}\t'
        str_times += f'{time / rep}\t'
    print(str_names)
    print(str_times)
