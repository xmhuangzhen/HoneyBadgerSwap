import re
import sys

idx_op = 1
idx_time = 3

idx_collect_keys_start = 1
idx_collect_keys_end = 2

idx_reserve_state_mask_start = 2
idx_reserve_state_mask_end = 3

idx_send_request_start = 3
idx_send_request_end = 4

idx_interpolate_start = 4
idx_interpolate_end = 5

idx_store_db_start = 5
idx_store_db_end = 6

idx_overall_start = 1
idx_overall_end = 6

if __name__ == '__main__':
    repetition = int(sys.argv[1])

    collect_keys = 0
    reserve_state_mask = 0
    send_request = 0
    interpolate = 0
    store_db = 0
    overall = 0

    file = f'ratel/benchmark/data/recover_states_{repetition}.csv'
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            element = re.split('\t|\n', line)

            op = int(element[idx_op])
            time = float(element[idx_time])
            print(op, time)

            if op == idx_collect_keys_start:
                collect_keys -= time
            if op == idx_collect_keys_end:
                collect_keys += time

            if op == idx_reserve_state_mask_start:
                reserve_state_mask -= time
            if op == idx_reserve_state_mask_end:
                reserve_state_mask += time

            if op == idx_send_request_start:
                send_request -= time
            if op == idx_send_request_end:
                send_request += time

            if op == idx_interpolate_start:
                interpolate -= time
            if op == idx_interpolate_end:
                interpolate += time

            if op == idx_store_db_start:
                store_db -= time
            if op == idx_store_db_end:
                store_db += time

            if op == idx_overall_start:
                overall -= time
            if op == idx_overall_end:
                overall += time

    print(f'overall\tcollect_keys\tsend_request\treserve_state_mask\tinterpolate\tstore_db')
    print(f'{overall}\t{collect_keys}\t{send_request}\t{reserve_state_mask}\t{interpolate}\t{store_db}')

