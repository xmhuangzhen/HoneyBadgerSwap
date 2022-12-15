#!/usr/bin/env bash
source ratel/src/utils.sh

set -e
set -x

##### fixed parameter
threshold=1
client_id=1
test_recover=1
token_num=0
concurrency=1
prog='rockPaperScissors'
#####
online_players=$1

./latency-control.sh stop

#rm -rf offline_data
bash ratel/src/deploy.sh $prog $token_num $online_players $threshold

refill $(($online_players+1))

ids=$(create_ids $online_players)
bash ratel/src/run.sh $prog $ids $online_players $threshold $concurrency $test_recover

python3 -m ratel.src.python.refill client_$client_id 0




