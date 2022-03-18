# Collateral auction


### 1 prerequesite

#### clone the repo
```
git clone https://github.com/xmhuangzhen/HoneyBadgerSwap.git
cd HoneyBadgerSwap
#git submodule update --init --recursive
```
#### install docker-engine
```
sudo apt-get remove docker docker.io containerd runc
sudo apt-get update
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```


#### install docker-compose
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```

### pull docker image & enter the container
```
sudo docker pull initc3/honeybadgerswap
sudo docker tag initc3/honeybadgerswap hbswap:latest
sudo docker-compose up -d

sudo docker exec -it honeybadgerswap_dev_1 bash
```
### compile the ratel
```
bash ratel/src/compile.sh colAuction
```


### Start local private blockchain and deploy application contract
```
bash ratel/src/deploy.sh colAuction 0 4 1
```

```
python3 -m ratel.src.python.refill server_0 0 \
& python3 -m ratel.src.python.refill server_1 0 \
& python3 -m ratel.src.python.refill server_2 0 \
& python3 -m ratel.src.python.refill server_3 0 
```

```
python3 -m ratel.src.python.refill client_1 0 \
& python3 -m ratel.src.python.refill client_2 0 \
& python3 -m ratel.src.python.refill client_3 0 \
& python3 -m ratel.src.python.refill client_4 0
```

```
bash ratel/src/run.sh colAuction 0,1,2,3 4 1 1 0
```

```
python3 -m ratel.src.python.colAuction.interact 

```