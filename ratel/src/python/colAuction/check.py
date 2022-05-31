import asyncio
from curses.ascii import SP
import time

from web3 import Web3
from web3.middleware import geth_poa_middleware

from ratel.src.python.Client import get_inputmasks, reserveInput
from ratel.src.python.deploy import url, app_addr
from ratel.src.python.utils import fp,parse_contract, getAccount, players, prime, sign_and_send

contract_name = 'colAuction'

liveAuct = []

# means I'll buy up to $amt if the prices reaches $price or below
def scheduleCheck(appContract,colAuctionId,account):

    curTime = web3.eth.block_number
    lastTime = appContract.functions.checkTime(colAuctionId).call()
    if(lastTime + 10 >= curTime):
        return

    web3.eth.defaultAccount = account.address
    tx = appContract.functions.scheduleCheck(colAuctionId).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    sign_and_send(tx, web3, account)
        
    

if __name__=='__main__':
    web3 = Web3(Web3.WebsocketProvider(url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract(contract_name)
    appContract = web3.eth.contract(address=app_addr, abi=abi)



    client_1 = getAccount(web3,f'/opt/poa/keystore/client_1/')
    client_2 = getAccount(web3,f'/opt/poa/keystore/client_2/')
    client_3 = getAccount(web3,f'/opt/poa/keystore/client_3/')
    client_4 = getAccount(web3,f'/opt/poa/keystore/client_4/')
    client_5 = getAccount(web3,f'/opt/poa/keystore/client_5/')
    client_6 = getAccount(web3,f'/opt/poa/keystore/client_6/')
    client_7 = getAccount(web3,f'/opt/poa/keystore/client_7/')
    client_8 = getAccount(web3,f'/opt/poa/keystore/client_8/')
    client_9 = getAccount(web3,f'/opt/poa/keystore/client_9/')
    client_10 = getAccount(web3,f'/opt/poa/keystore/client_10/')
    clients = [client_1,client_2,client_3,client_4,client_5,client_6,client_7,client_8,client_9,client_10]
    n_cli = len(clients)

    cur_cli = 0
    cur_n = 0

    ccnt = 0

    while True:
        #refresh liveAuct[]
        while True:
            status = appContract.functions.status(cur_n+1).call()
            if status >= 1:
                cur_n += 1
                liveAuct.append(cur_n)
                print("cur Live Auct Id(adding):",liveAuct)
            else:
                break
        
        for aucId in liveAuct:
            status = appContract.functions.status(aucId).call()
            if status == 1:
                liveAuct.remove(aucId)
                print("cur Live Auct Id(removing):",liveAuct)
        
        if ccnt == 1000:
            ccnt = 0
            print("curLiveAuctionId:",liveAuct)

        for aucId in liveAuct:
            scheduleCheck(appContract,aucId,clients[cur_cli])

        time.sleep(60)
        ccnt = ccnt+1
        cur_cli = (cur_cli + 1) % n_cli

    

