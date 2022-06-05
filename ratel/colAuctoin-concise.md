# Collateral auction


```
git clone https://github.com/xmhuangzhen/HoneyBadgerSwap.git
cd HoneyBadgerSwap
git checkout app10
```

```
sudo docker-compose build
sudo docker-compose up -d
sudo docker exec -it honeybadgerswap_dev_1 bash
```

```
bash setup-ssl.sh 4
bash ratel/src/compile.sh colAuction
pip install pybulletproofs
bash ratel/src/deploy.sh colAuction 0 4 1
python3 -m ratel.src.python.refill server_0 0 \
& python3 -m ratel.src.python.refill server_1 0 \
& python3 -m ratel.src.python.refill server_2 0 \
& python3 -m ratel.src.python.refill server_3 0 
python3 -m ratel.src.python.refill client_1 0 \
& python3 -m ratel.src.python.refill client_2 0 \
& python3 -m ratel.src.python.refill client_3 0 \
& python3 -m ratel.src.python.refill client_4 0 \
& python3 -m ratel.src.python.refill client_5 0
python3 -m ratel.src.python.refill client_6 0 \
& python3 -m ratel.src.python.refill client_7 0 \
& python3 -m ratel.src.python.refill client_8 0 \
& python3 -m ratel.src.python.refill client_9 0 \
& python3 -m ratel.src.python.refill client_10 0
python3 -m ratel.src.python.refill client_11 0 \
& python3 -m ratel.src.python.refill client_12 0 \
& python3 -m ratel.src.python.refill client_13 0 \
& python3 -m ratel.src.python.refill client_14 0 \
& python3 -m ratel.src.python.refill client_15 0
python3 -m ratel.src.python.refill client_16 0 \
& python3 -m ratel.src.python.refill client_17 0 \
& python3 -m ratel.src.python.refill client_18 0 \
& python3 -m ratel.src.python.refill client_19 0 \
& python3 -m ratel.src.python.refill client_20 0

bash ratel/src/run.sh colAuction 0,1,2,3 4 1 1 0

python3 -m ratel.src.python.colAuction.check & 
python3 -m ratel.src.python.colAuction.interact 
```
