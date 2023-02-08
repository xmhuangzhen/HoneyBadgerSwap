#!/usr/bin/env bash
source ratel/src/utils.sh

set -e
set -x

##### fixed parameter
threshold=1
concurrency=1
client_id=1
value=1
one=1
test_recover=1
app='rockPaperScissors'
#####

##### get argv
online_players=$1
repetition=$2
rep=$3
latency=${4:-0}
#####

mkdir -p ratel/benchmark/data

ids=$(create_ids $online_players)

for ((i = 0; i < rep; i++)) do

  bash latency-control.sh stop || true

  bash ratel/src/run.sh $app $ids $online_players $threshold $concurrency $test_recover

  if [[ $latency -eq $one ]]; then
    bash latency-control.sh start 100ms $online_players $concurrency
  fi

  python3 -m ratel.src.python.rockPaperScissors.create_game $client_id $value

  python3 -m ratel.benchmark.src.test_recover_states $online_players $online_players $threshold $concurrency $repetition &

  sleep 30
done
