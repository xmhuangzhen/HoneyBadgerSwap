#!/usr/bin/env bash

set -e
set -x

POADIR=${POADIR:-/opt/poa}
KEYSTORE=${POA_KEYSTORE:-/opt/poa/keystore/admin}
DATADIR=${POA_DATADIR:-/opt/poa/data}

pkill -f geth

sleep 1

rm -rf $DATADIR
mkdir $DATADIR

geth --datadir $DATADIR init $POADIR/genesis.json

geth \
    --datadir $DATADIR \
    --keystore $KEYSTORE \
    --mine --allow-insecure-unlock --unlock 0 \
    --password $POADIR/empty_password.txt \
    --http \
    --http.addr 0.0.0.0 \
    --http.corsdomain '*' \
    --http.api admin,debug,eth,miner,net,personal,shh,txpool,web3 \
    --ws \
    --ws.addr 0.0.0.0 \
    --ws.origins '*' \
    --ws.api admin,debug,eth,miner,net,personal,shh,txpool,web3 \
    --syncmode full \
    --ipcpath "$DATADIR/geth.ipc" \
    2>> $DATADIR/geth.log &

sleep 3
