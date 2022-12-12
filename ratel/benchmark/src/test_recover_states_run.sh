#!/usr/bin/env bash
source ratel/src/utils.sh

set -e
set -x

##### fixed parameter
threshold=1
concurrency=1
#####

online_players=$1
repetion=$2


#./latency-control.sh start 200 50

python3 -m ratel.benchmark.src.test_recover_states $(($online_players)) $online_players $threshold $concurrency $repetion

#./latency-control.sh stop