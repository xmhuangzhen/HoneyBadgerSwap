#!/usr/bin/env bash
#####
##### ./ratel/benchmark/src/test_real_data_trade_run.sh
#####

set -e
set -x

source ratel/src/utils.sh

##### fixed parameter
threshold=1
token_A_id=0
test_recover=0
pool_name='traderjoev2_USDC.e_WAVAX'
client_num=1
concurrency=1
#####

##### get argv
players=$1
duration=$2
#####

mkdir -p ratel/benchmark/data
for ((server_id = 0; server_id < $players; server_id++ )) do
  rm ratel/benchmark/data/latency*_$server_id.csv || true
done
rm ratel/benchmark/data/gas.csv || true
rm ratel/benchmark/data/fig.pdf || true

bash latency-control.sh stop || true

ids=$(create_ids $players)
bash ratel/src/run.sh hbswap $ids $players $threshold $concurrency $test_recover

bash latency-control.sh start 100ms $players $concurrency

python3 -m ratel.benchmark.src.swap.run $pool_name $duration &
