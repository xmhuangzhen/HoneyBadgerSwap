### Compile ratel program
```shell
bash ratel/src/compile.sh [app_names] [finalize_on_chain(0 or 1)]
```
```shell
bash ratel/src/compile.sh rockPaperScissors 1
```

### Set up SSL keys for 4 servers
```shell
bash setup-ssl.sh 4 [directory] 
```
```shell
bash setup-ssl.sh 4 /opt/ssl
```

### Start local private blockchain and deploy application contract with ONLY 3 servers
```shell
bash ratel/src/deploy.sh [app_name] [token_num] [MPC_server_number] [threshold]
```
```shell
bash ratel/src/deploy.sh rockPaperScissors 0 4 1
```

### Transfer Ether(token_id=0) to MPC servers and clients for them to pay transaction fee
```shell
python3 -m ratel.src.python.refill [user_name (see available choices in poa/keystore/)] [token_id]
```
```shell
python3 -m ratel.src.python.refill server_0 0 \
& python3 -m ratel.src.python.refill server_1 0 \
& python3 -m ratel.src.python.refill server_2 0 \
& python3 -m ratel.src.python.refill server_3 0
```
```shell
python3 -m ratel.src.python.refill client_1 0 \
& python3 -m ratel.src.python.refill client_2 0
```

### Start ALL MPC servers
```shell
bash ratel/src/run.sh [app_name] [MPC_server_IDs] [MPC_server_number] [threshold] [concurrency] [test_flag]
```
```shell
bash ratel/src/run.sh rockPaperScissors 0,1,2,3 4 1 1 0
```

### Kill the 4-th server
```shell
pkill -f 'python3 -m ratel.src.python.rockPaperScissors.run 3'
```

#### Create game by a client
```shell
python3 -m ratel.src.python.rockPaperScissors.create_game [cilent_id] [value] 
```
```shell
python3 -m ratel.src.python.rockPaperScissors.create_game 1 1 
```

#### Re-start the 4-th MPC server
```shell
python3 -m ratel.src.python.rockPaperScissors.run [MPC_server_ID] [MPC_server_number] [threshold] [concurrency] [test_flag]
```
```shell
python3 -m ratel.src.python.rockPaperScissors.run 3 4 1 1 0 > ratel/log/server_3.log 2>&1 &
```

#### Join game by another client
```shell
python3 -m ratel.src.python.rockPaperScissors.end_game [client_id] [value] [game_id]
```
```shell
python3 -m ratel.src.python.rockPaperScissors.end_game 2 2 1 
```

#### Kill 3-th server
```shell
pkill -f 'python3 -m ratel.src.python.rockPaperScissors.run 2'
```

#### Create game by a client
```shell
python3 -m ratel.src.python.rockPaperScissors.create_game 1 1 
```

#### Recover 3-th server
```shell
python3 -m ratel.src.python.rockPaperScissors.run 2 4 1 1 0 > ratel/log/server_2.log 2>&1 &
```

#### Join game by another client
```shell
python3 -m ratel.src.python.rockPaperScissors.end_game 2 2 1 
```


