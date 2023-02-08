# HoneyBadgerSwap

`docker-compose build`

`docker-compose up -d`

`docker exec -it honeybadgerswap_dev_1 bash`

`bash setup-ssl.sh 4 /opt/ssl`

`bash ratel/src/compile.sh hbswap_zkp`

`bash ratel/src/deploy.sh hbswap_zkp 1 4 1`

```
python3 -m ratel.src.python.refill server_0 0 &
python3 -m ratel.src.python.refill server_1 0 &
python3 -m ratel.src.python.refill server_2 0 &
python3 -m ratel.src.python.refill server_3 0 &
python3 -m ratel.src.python.refill client_1 0 &
python3 -m ratel.src.python.refill client_1 1
```

`bash ratel/src/run.sh hbswap_zkp 0,1,2,3 4 1 1 0`

```
python3 -m ratel.src.python.hbswap_zkp.deposit 1 0 10000
python3 -m ratel.src.python.hbswap_zkp.deposit 1 1 10000
```

`python3 -m ratel.src.python.hbswap_zkp.initPool 1 0 1 1000 1000`

`python3 -m ratel.src.python.hbswap_zkp.trade 1 0 1 0.5 -1 1`


Test
```bash
./ratel/benchmark/src/test_concurrent_trade_start.sh [players] [client_num] [concurrency] [app]
./ratel/benchmark/src/test_concurrent_trade_run.sh [players] [client_num] [concurrency] [rep] [app]
```

Test Single Trade
```bash
./ratel/benchmark/src/test_concurrent_trade_start.sh 4 1 1 hbswap_zkp
./ratel/benchmark/src/test_concurrent_trade_run.sh 4 1 1 5 hbswap_zkp
```

Analyze
```
python -m ratel.benchmark.src.trade_latency [players] [dir] [prog]
python -m ratel.benchmark.src.trade_latency 4 ratel/benchmark/data hbswap_zkp
```
