import asyncio
from curses.ascii import SP
import time

from web3 import Web3
from web3.middleware import geth_poa_middleware

from ratel.src.python.Client import get_inputmasks, reserveInput
from ratel.src.python.deploy import url, app_addr, token_addrs
from ratel.src.python.utils import fp,parse_contract, getAccount, players, prime, sign_and_send, threshold

contract_name = 'colAuction'

bids_cnt = []

def initClient(appContract,account,token_addr,user_addr):
    web3.eth.defaultAccount = account.address
    tx = appContract.functions.initClient(token_addr,user_addr).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    sign_and_send(tx, web3, account)


def createAuction(appContract,StartPrice,FloorPrice,totalAmt,token,aucapp_addr,creator_addr,account):
    colAuctionlast = appContract.functions.colAuctionCnt().call()

    bids_cnt.append(0)

    web3.eth.defaultAccount = account.address
    tx = appContract.functions.createAuction(StartPrice,FloorPrice,totalAmt,token,aucapp_addr,creator_addr).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    sign_and_send(tx, web3, account)

    while True:
        colAuctionId = appContract.functions.colAuctionCnt().call()
        time.sleep(1)
        status = appContract.functions.status(colAuctionId).call()
        if status == 2 and colAuctionId != colAuctionlast:
            return colAuctionId



# means I'll buy up to $amt if the prices reaches $price or below
def submitBids(appContract,colAuctionId,price,amt,bidder_addr,account):
    status = appContract.functions.status(colAuctionId).call()
    if status == 1:
        return

    cur_bidcnt = bids_cnt[colAuctionId-1]
    print("curbid cnt",colAuctionId,cur_bidcnt)


    idx1, idx2 = reserveInput(web3, appContract, 2, account)
    mask1, mask2 = asyncio.run(get_inputmasks(players(appContract), f'{idx1},{idx2}', threshold(appContract)))
    maskedP, maskedAmt = (price + mask1) % prime, (amt + mask2) % prime

    web3.eth.defaultAccount = account.address
    tx = appContract.functions.submitBids(colAuctionId, idx1, maskedP, idx2, maskedAmt,bidder_addr).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    sign_and_send(tx, web3, account)

    while True:
        time.sleep(1)
        status = appContract.functions.status(colAuctionId).call()
        if status-2 > cur_bidcnt:
            bids_cnt[colAuctionId-1] = status-2
            return
        if status == 1:
            return



if __name__=='__main__':
    web3 = Web3(Web3.WebsocketProvider(url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract(contract_name)
    appContract = web3.eth.contract(address=app_addr, abi=abi)


    file = open('ratel/src/python/colAuction/aucdata.txt', 'r')
    tmp_list = file.readline().strip('\n').split(',')

    start_t = int(tmp_list[0]); StartPrice = int(tmp_list[1])
    FloorPrice = 2000; totalAmt = int(float(tmp_list[3])*100)
    creator_addr = Web3.toChecksumAddress(tmp_list[4])
    aucapp_addr = Web3.toChecksumAddress(tmp_list[5])
    # print(start_t,StartPrice,totalAmt,app_addr)

    start_time = time.time()
    cur_time = time.strftime("%D %H:%M:%S",time.localtime())
    with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
        f.write(f'start!\t'
                f'cur_time\t{cur_time}\n')



    client_8 = getAccount(web3,f'/opt/poa/keystore/client_8/')
    client_9 = getAccount(web3,f'/opt/poa/keystore/client_9/')
    client_10 = getAccount(web3,f'/opt/poa/keystore/client_10/')
    client_11 = getAccount(web3,f'/opt/poa/keystore/client_11/')
    client_12 = getAccount(web3,f'/opt/poa/keystore/client_12/')
    client_13 = getAccount(web3,f'/opt/poa/keystore/client_13/')
    client_14 = getAccount(web3,f'/opt/poa/keystore/client_14/')
    client_15 = getAccount(web3,f'/opt/poa/keystore/client_15/')
    client_16 = getAccount(web3,f'/opt/poa/keystore/client_16/')
    client_17 = getAccount(web3,f'/opt/poa/keystore/client_17/')
    client_18 = getAccount(web3,f'/opt/poa/keystore/client_18/')
    client_19 = getAccount(web3,f'/opt/poa/keystore/client_19/')
    client_20 = getAccount(web3,f'/opt/poa/keystore/client_20/')


    clients=[client_8,client_9,client_10,client_11,client_12,client_13,client_14,client_15,client_16,client_17,client_18,client_19,client_20]
    n_cli = len(clients)

    initClient(appContract,clients[0],token_addrs[0],creator_addr)
    initClient(appContract,clients[0],token_addrs[1],creator_addr)

    cur_time = time.strftime("%D %H:%M:%S",time.localtime())
    with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
        f.write(f'create_auction\t'
                f'cur_time\t{cur_time}\n')


    colAuctionId1 = createAuction(appContract,StartPrice,FloorPrice,totalAmt,token_addrs[1],aucapp_addr,creator_addr,clients[0])
    print('new Auction id:',colAuctionId1)

    cur_cli = 1
    cnt = 0 

    while True:
        cnt = cnt + 1
        
        tmp_list = file.readline().strip('\n').split(',')

        if len(tmp_list) == 0:
            break

        ti = int(tmp_list[0])
        pricei = int(tmp_list[1])
        amti = int(float(tmp_list[2])*100)
        addri = Web3.toChecksumAddress(tmp_list[4])

        initClient(appContract,clients[cur_cli],token_addrs[0],addri)
        initClient(appContract,clients[cur_cli],token_addrs[1],addri)

        cur_time = time.time()
        # print(cur_time,start_time,ti)
        while cur_time - start_time < ti:
            time.sleep(1)
            cur_time = time.time()
        
        with open(f'ratel/benchmark/data/latency.csv', 'a') as f:
            f.write(f'start_submit_bids\t'
                    f'cur_time\t{cur_time}\n')


        submitBids(appContract,colAuctionId1,pricei,amti,addri,clients[cur_cli])
        cur_cli = (cur_cli + 1) % n_cli
        print('finished input bidders ',cnt)
