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
#####

online_players=$1
repetion=$2
lantecy=${3:-0}

rm ratel/benchmark/data/recover_states_* || true
mkdir -p ratel/benchmark/data

./latency-control.sh stop
if [[ $lantecy -eq $one ]]; then
    ./latency-control.sh start 200 50
fi

python3 -m ratel.src.python.rockPaperScissors.create_game $client_id $value

python3 -m ratel.benchmark.src.test_recover_states $online_players $online_players $threshold $concurrency $repetion
