#!/usr/bin/env bash
#####
##### ./ratel/benchmark/src/test_concurrent_trade_run.sh
#####

set -e
set -x

source ratel/src/utils.sh

##### fixed parameter
threshold=1
token_A_id=0
test_recover=0
#####

##### get argv
players=$1
client_num=$2
concurrency=$3
rep=$4
app=$5
#####

mkdir -p ratel/benchmark/data
for ((server_id = 0; server_id < $players; server_id++ )) do
  rm ratel/benchmark/data/latency*_$server_id.csv || true
done
rm ratel/benchmark/data/gas.csv || true
rm ratel/benchmark/data/fig.pdf || true

bash latency-control.sh stop || true

python3 -m ratel.benchmark.src.set_up_offline_data $players $threshold $concurrency

ids=$(create_ids $players)
bash ratel/src/run.sh $app $ids $players $threshold $concurrency $test_recover

bash latency-control.sh start 100ms $players $concurrency

for (( client_id = 1; client_id <= $client_num; client_id++ )) do
  token_B_id=$client_id
  python3 -m ratel.src.python.$app.trade $client_id $token_A_id $token_B_id 0.5 -1 $rep &
  sleep 1
done

