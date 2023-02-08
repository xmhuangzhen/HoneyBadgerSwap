# HoneyBadgerSwap

`docker-compose build`

`docker-compose up -d`

`docker exec -it honeybadgerswap_dev_1 bash`

`bash setup-ssl.sh 4 /opt/ssl`

`bash ratel/src/compile.sh hbswap`

`bash ratel/src/deploy.sh hbswap 1 4 1`

```
python3 -m ratel.src.python.refill server_0 0 &
python3 -m ratel.src.python.refill server_1 0 &
python3 -m ratel.src.python.refill server_2 0 &
python3 -m ratel.src.python.refill server_3 0 &
python3 -m ratel.src.python.refill client_1 0 &
python3 -m ratel.src.python.refill client_1 1
```

`bash ratel/src/run.sh hbswap 0,1,2,3 4 1 1 0`

```
python3 -m ratel.src.python.hbswap.deposit 1 0 10000
python3 -m ratel.src.python.hbswap.deposit 1 1 10000
```

`python3 -m ratel.src.python.hbswap.initPool 1 0 1 1000 1000`

`python3 -m ratel.src.python.hbswap.trade 1 0 1 0.5 -1 1`

`python3 -m ratel.src.python.hbswap.withdraw 1 0 2000`



[//]: # (Test concurrency:)

[//]: # (```)

[//]: # (bash ratel/src/deploy.sh hbswap 4 1)

[//]: # ()
[//]: # (bash ratel/src/run.sh hbswap 0,1,2,3 4 1)

[//]: # ()
[//]: # (python3 -m ratel.src.python.hbswap.deposit 0x0000000000000000000000000000000000000000 1 &)

[//]: # (python3 -m ratel.src.python.hbswap.deposit 0xF74Eb25Ab1785D24306CA6b3CBFf0D0b0817C5E2 1 &)

[//]: # (python3 -m ratel.src.python.hbswap.deposit 0x0000000000000000000000000000000000000000 1 &)

[//]: # (python3 -m ratel.src.python.hbswap.deposit 0xF74Eb25Ab1785D24306CA6b3CBFf0D0b0817C5E2 1 &)

[//]: # ()
[//]: # (python3 -m ratel.src.python.hbswap.deposit 0x0000000000000000000000000000000000000000 1 &)

[//]: # (python3 -m ratel.src.python.hbswap.deposit 0x0000000000000000000000000000000000000000 1 &)

[//]: # (python3 -m ratel.src.python.hbswap.deposit 0x0000000000000000000000000000000000000000 1 &)

[//]: # ()
[//]: # (```)

Introduce latency:
```bash
bash latency-control.sh start [latency] [players] [concurrency] (w/ jitter=5ms)
bash latency-control.sh start 100ms 4 1
```

Test
```bash
./ratel/benchmark/src/test_concurrent_trade_start.sh [players] [client_num] [concurrency] [app]
./ratel/benchmark/src/test_concurrent_trade_run.sh [players] [client_num] [concurrency] [rep] [app]
```

Test single trade
```
./ratel/benchmark/src/test_concurrent_trade_start.sh 4 1 1 hbswap
./ratel/benchmark/src/test_concurrent_trade_run.sh 4 1 1 5 hbswap
```

Test concurrent trade
```bash
./ratel/benchmark/src/test_concurrent_trade_start.sh 4 20 20 hbswap

./ratel/benchmark/src/test_concurrent_trade_run.sh 4 10 1 2 hbswap
./ratel/benchmark/src/test_concurrent_trade_run.sh 4 10 2 4 hbswap
./ratel/benchmark/src/test_concurrent_trade_run.sh 4 10 4 8 hbswap
./ratel/benchmark/src/test_concurrent_trade_run.sh 4 10 8 16 hbswap
./ratel/benchmark/src/test_concurrent_trade_run.sh 4 20 16 32 hbswap
```
Calculate Latency
```
python -m ratel.benchmark.src.trade_latency [players] [path] [prog]
python -m ratel.benchmark.src.trade_latency 4 ratel/benchmark/data hbswap
```
Calculate throughput
```
python -m ratel.benchmark.src.trade_throughput [path] [prog]
python -m ratel.benchmark.src.trade_throughput ratel/benchmark/data hbswap
```
Plot currency performance (run on local machine)
```
python3 -m ratel.benchmark.src.trade_plot
```

Test Real-world Data
```
./ratel/benchmark/src/test_concurrent_trade_start.sh 4 1 1 hbswap

./ratel/benchmark/src/swap/test_real_data_trade_run.sh [players] [duration]
./ratel/benchmark/src/swap/test_real_data_trade_run.sh 4 60
./ratel/benchmark/src/swap/test_real_data_trade_run.sh 4 3600
```
Calculate running time pdf
```
python3 -m ratel.benchmark.src.swap.collect [players] [path]
python3 -m ratel.benchmark.src.swap.collect 4 ratel/benchmark/data
python3 -m ratel.benchmark.src.swap.collect 4 ratel/benchmark/data/read_world_1_hour
```
Draw performance over real-world data
```
python3 -m ratel.benchmark.src.swap.analyze [players] [path]
python3 -m ratel.benchmark.src.swap.analyze 4 ratel/benchmark/data
python3 -m ratel.benchmark.src.swap.analyze 4 ratel/benchmark/data/read_world_1_hour
```
Simulate 3-days running over real-world data
```
python3 -m ratel.benchmark.src.swap.simulate [start_time] [end_time] [pool_name]
python3 -m ratel.benchmark.src.swap.simulate 172800 432000 traderjoev2_USDC.e_WAVAX
```

Test recover states
```bash

bash ratel/benchmark/src/crash/test_recover_states_start.sh [online_players] (recover another player)
bash ratel/benchmark/src/crash/test_recover_states_start.sh 3

bash ratel/benchmark/src/crash/test_recover_states_run.sh [online_players] [repetition] [whether introduce latency]

bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 100 5 0
bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 1000 5 0
bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 2000 5 0
bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 4000 5 0

bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 1000 5 1
bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 2000 5 1
bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 4000 5 1

python3 -m ratel.benchmark.src.crash.recover_states_plot [repetition] [rep]
python3 -m ratel.benchmark.src.crash.recover_states_plot 100 5
python3 -m ratel.benchmark.src.crash.recover_states_plot 1000 5
python3 -m ratel.benchmark.src.crash.recover_states_plot 2000 5
python3 -m ratel.benchmark.src.crash.recover_states_plot 4000 5

bash ratel/benchmark/src/crash/test_recover_states_run.sh 3 100 1 0

```

Test MP-SPDZ concurrency
```bash
python3 -m ratel.benchmark.src.test_mpc
```
