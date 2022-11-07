import asyncio
import sys
import time
import json

from web3 import Web3
from web3.middleware import geth_poa_middleware
from ratel.src.python.Client import get_inputmasks, reserveInput, get_poolval
from ratel.src.python.deploy import url, app_addr, token_addrs
from ratel.src.python.utils import fp, prime, getAccount, sign_and_send, parse_contract, players, threshold, get_zkrp


def trade(appContract, tokenA, tokenB, amtA, amtB, account, web3, client_id):

    ###############zkrp prove here#############
    poolA, poolB = asyncio.run(get_poolval(players(appContract), tokenA, tokenB, threshold(appContract)))
    poolA = float(poolA / fp)
    poolB = float(poolA / fp)
    poolProduct = poolA * poolB
    actualAmtA = poolA - poolProduct / (poolB - amtB)
    actualAmtB = poolB - poolProduct / (poolA - amtA)

    print('actualAmtA:',actualAmtA, 'actualAmtB', actualAmtB)

    proof1, commitment1, blinding1 = get_zkrp(amtA, '>', 0, True)
    proof2, commitment2, blinding2 = get_zkrp(amtB, '>', 0, True)
    proof3, commitment3, blinding3 = get_zkrp(actualAmtA, '>=', amtA, True) # acceptA = zkrp(actualAmtA >= amtA)
    proof4, commitment4, blinding4 = get_zkrp(actualAmtB, '>=', amtB, True) # acceptB = zkrp(actualAmtB >= amtB)
    ###############zkrp prove end#############

    amtA = int(amtA * fp)
    amtB = int(amtB * fp)
    
    idxAmtA, idxAmtB, idxzkp1, idxzkp2, idxzkp3, idxzkp4 = reserveInput(web3, appContract, 6, account)
    maskA, maskB, maskzkp1, maskzkp2, maskzkp3, maskzkp4 = asyncio.run(get_inputmasks(players(appContract), f'{idxAmtA},{idxAmtB},{idxzkp1},{idxzkp2},{idxzkp3},{idxzkp4}', threshold(appContract)))
    maskedAmtA, maskedAmtB, maskedzkp1, maskedzkp2, maskedzkp3, maskedzkp4 = (amtA + maskA) % prime, (amtB + maskB) % prime, (blinding1 + maskzkp1) % prime, (blinding2 + maskzkp2) % prime, (blinding3 + maskzkp3) % prime, (blinding4 + maskzkp4) % prime

    zkp1 = [idxzkp1,maskedzkp1,proof1,commitment1]
    zkp2 = [idxzkp2,maskedzkp2,proof2,commitment2]
    zkp3 = [idxzkp3,maskedzkp3,proof3,commitment3]
    zkp4 = [idxzkp4,maskedzkp4,proof4,commitment4]
    zkps = json.dumps([zkp1,zkp2,zkp3,zkp4])

    tx = appContract.functions.trade(tokenA, tokenB, idxAmtA, maskedAmtA, idxAmtB, maskedAmtB, zkps).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    receipt = sign_and_send(tx, web3, account)
    log = appContract.events.Trade().processReceipt(receipt)[0]
    print(log['args'])
    seqTrade = log['args']['seqTrade']
    with open('ratel/benchmark/data/gas.csv', 'a') as f:
        f.write(f"trade\t{seqTrade}\t"
                f"client\t{client_id}\t"
                f"tokenA\t{tokenA}\t"
                f"tokenB\t{tokenB}\t"
                f"gasUsed\t{receipt['gasUsed']}\t"
                f"{time.perf_counter()}\n")


if __name__=='__main__':
    client_id = int(sys.argv[1])
    tokenA = token_addrs[int(sys.argv[2])]
    tokenB = token_addrs[int(sys.argv[3])]
    amtA = float(sys.argv[4])
    amtB = float(sys.argv[5])
    repetition = int(sys.argv[6])

    web3 = Web3(Web3.WebsocketProvider(url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract('hbswap')
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    account = getAccount(web3, f'/opt/poa/keystore/client_{client_id}/')
    web3.eth.defaultAccount = account.address

    for i in range(repetition):
        trade(appContract, tokenA, tokenB, amtA, amtB, account, web3, client_id)
        trade(appContract, tokenA, tokenB, amtB, amtA, account, web3, client_id)
