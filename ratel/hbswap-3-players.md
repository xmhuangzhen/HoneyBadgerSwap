

`docker-compose build`

`docker-compose up -d --force-recreate`

`docker exec -it honeybadgerswap_dev_1 bash`

`bash setup-ssl.sh 3`

`bash ratel/src/compile.sh hbswap`

```
./ratel/benchmark/src/test_concurrent_trade_start.sh [players] [client_num] [concurrency]

./ratel/benchmark/src/test_concurrent_trade_start.sh 3 1 1
./ratel/benchmark/src/test_concurrent_trade_start.sh 3 2 2
./ratel/benchmark/src/test_concurrent_trade_start.sh 3 4 4
./ratel/benchmark/src/test_concurrent_trade_start.sh 3 8 8
./ratel/benchmark/src/test_concurrent_trade_start.sh 3 16 16
```

```
./ratel/benchmark/src/test_concurrent_trade_run.sh [players] [client_num] [concurrency] [rep]

./ratel/benchmark/src/test_concurrent_trade_run.sh 3 1 1 1
./ratel/benchmark/src/test_concurrent_trade_run.sh 3 2 2 10
./ratel/benchmark/src/test_concurrent_trade_run.sh 3 4 4 10
./ratel/benchmark/src/test_concurrent_trade_run.sh 3 16 16 10
```

`python3 -m ratel.benchmark.src.plot ratel/benchmark/data`

```
python3 -m ratel.benchmark.src.calc [players] [dir]
python3 -m ratel.benchmark.src.calc 3 ratel/benchmark/data
```

`./latency-control.sh stop`

`./latency-control.sh start 200 50`

```
./compile.py -v -C -F 128 ratel/genfiles/mpc/hbswapTrade1.mpc
python3 -m ratel.benchmark.src.test_mpc 3 1 10
```

```
./ratel/benchmark/src/test_inputmask_generation_run.sh
```

```
python3 -m ratel.src.python.hbswap.updateBatchPrice
```
