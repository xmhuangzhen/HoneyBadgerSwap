import re
import sys

idx_op = 1
idx_time = 3

idx_reserve_state_mask_start = 2
idx_reserve_state_mask_end = 3

idx_send_request_start = 3
idx_send_request_end = 4

idx_overall_start = 1
idx_overall_end = 6

if __name__ == '__main__':
    repetition = int(sys.argv[1])

    reserve_state_mask = 0
    send_request = 0
    overall = 0

    file = f'ratel/benchmark/data/recover_states_{repetition}.csv'
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            element = re.split('\t|\n', line)

            op = int(element[idx_op])
            time = float(element[idx_time])
            print(op, time)

            if op == idx_reserve_state_mask_start:
                reserve_state_mask -= time
            if op == idx_reserve_state_mask_end:
                reserve_state_mask += time

            if op == idx_send_request_start:
                send_request -= time
            if op == idx_send_request_end:
                send_request += time

            if op == idx_overall_start:
                overall -= time
            if op == idx_overall_end:
                overall += time

    print(f'overall\tsend_request\treserve_state_mask')
    print(f'{overall}\t{send_request}\t{reserve_state_mask}')

