#!/usr/bin/env bash
#####
##### ./ratel/benchmark/src/test_concurrent_trade_run.sh
#####

set -e
set -x

##### fixed parameter
players=4
threshold=1
token_A_id=0
#####

client_num=$1
concurrency=$2
rep=$3

bash ratel/src/run.sh hbswap 0,1,2,3 $players $threshold $concurrency

for ((server_id = 0; server_id < $players; server_id++ )) do
  rm ratel/benchmark/data/latency_$server_id.csv || true
done
rm ratel/benchmark/data/gas.csv || true
rm ratel/benchmark/data/fig.pdf || true

sleep 10

for (( client_id = 1; client_id <= $client_num; client_id++ )) do
  token_B_id=$client_id
  python3 -m ratel.src.python.hbswap.trade $client_id $token_A_id $token_B_id 0.5 -1 $rep &
  sleep 1
done