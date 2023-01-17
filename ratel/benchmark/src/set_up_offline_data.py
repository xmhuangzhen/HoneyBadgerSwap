import asyncio
import os
import sys

from ratel.benchmark.src.test_mpc import run_test
from ratel.src.python.utils import mpc_port, execute_cmd


def check_exist(mpc_prog, port, server_id):
    dir = f'offline_data/s{server_id}/{mpc_prog}_port_{port}'
    return os.path.exists(dir)


def duplicate_offline_data(mpc_prog, players, concurrency):
    for i in range(-1, concurrency):
        port = mpc_port + i * 100

        for server_id in range(players):
            if check_exist(mpc_prog, port, server_id):
                continue

            src_dir = f'offline_data/s{server_id}/{mpc_prog}_port_{mpc_port}'
            dst_dir = f'offline_data/s{server_id}/{mpc_prog}_port_{port}'

            cmd = f'cp -rf {src_dir} {dst_dir}'
            asyncio.run(execute_cmd(cmd))


def set_offline_data(players, threshold, concurrency):
    directory = os.fsencode(f'ratel/genfiles/mpc')

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".mpc"):
            mpc_prog = filename[:-4]
            if not check_exist(mpc_prog, mpc_port, 0):
                asyncio.run(run_test('run_offline', players, threshold, 1, mpc_prog))
            duplicate_offline_data(mpc_prog, players, concurrency)


if __name__ == '__main__':
    players = int(sys.argv[1])
    threshold = int(sys.argv[2])
    concurrency = int(sys.argv[3])

    set_offline_data(players, threshold, concurrency)




