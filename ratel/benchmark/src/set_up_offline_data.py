import asyncio
import os
import sys

from ratel.benchmark.src.test_mpc import run_test
from ratel.src.python.utils import mpc_port, execute_cmd

if __name__ == '__main__':
    players = int(sys.argv[1])
    threshold = int(sys.argv[2])
    concurrency = int(sys.argv[3])

    directory = os.fsencode(f'ratel/genfiles/mpc')

    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".mpc"):
            mpc_prog = filename[:-4]
            asyncio.run(run_test('run_offline', players, threshold, 1, mpc_prog))
            for i in range(1, concurrency):
                port = mpc_port + i * 100

                src_dir = f'offchain-data/{mpc_prog}-Player-data-port-{mpc_port}'
                dst_dir = f'offchain-data/{mpc_prog}-Player-data-port-{port}'

                cmd = f'cp -rf {src_dir} {dst_dir}'
                asyncio.run(execute_cmd(cmd))


