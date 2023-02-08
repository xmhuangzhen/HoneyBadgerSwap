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
app='rockPaperScissors'
finalize_on_chain=1
#####

##### get argv
online_players=$1
#####

rm ratel/benchmark/data/recover_states_* || true
bash latency-control.sh stop || true
rm -rf offline_data

bash setup-ssl.sh $(($online_players+1)) /opt/ssl
bash ratel/src/compile.sh $app $finalize_on_chain

bash ratel/src/deploy.sh $app $token_num $online_players $threshold

refill $(($online_players+1))

ids=$(create_ids $online_players)
bash ratel/src/run.sh $app $ids $online_players $threshold $concurrency $test_recover

python3 -m ratel.src.python.refill client_$client_id 0




