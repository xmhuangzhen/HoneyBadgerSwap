import asyncio
import sys
import time
import json

from web3 import Web3
from web3.middleware import geth_poa_middleware
from ratel.src.python.Client import get_inputmasks, reserveInput, get_secret_values
from ratel.src.python.deploy import ws_provider, app_addr, token_addrs
from ratel.src.python.utils import fp, prime, getAccount, sign_and_send, parse_contract, players, threshold, get_zkrp, generate_zkrp_mul


def trade(appContract, tokenA, tokenB, amtA, amtB, account, web3, client_id):
    amtA = int(amtA * fp)
    amtB = int(amtB * fp)

    times = []
    times.append(time.perf_counter())

    ###############zkrp prove here#############
    key_balance_A = f'balance_{tokenA}_{account.address}'
    key_balance_B = f'balance_{tokenB}_{account.address}'

    balanceA, balanceB = get_secret_values(players(appContract), f'{key_balance_A},{key_balance_B}', threshold(appContract))

    feeRate = 0
    totalA = (1 + feeRate) * amtA
    totalB = (1 + feeRate) * amtB

    Cz, Prf1, rx, ry = generate_zkrp_mul(amtA, amtB, '<=', 0)
    proof2, commitment2, blinding2 = get_zkrp(-totalA, '<=', balanceA)
    proof3, commitment3, blinding3 = get_zkrp(-totalB, '<=', balanceB)

    ###############zkrp prove end#############
    times.append(time.perf_counter())
    with open(f'ratel/benchmark/data/latency_client.csv', 'a') as f:
        for op, t in enumerate(times):
            f.write(f'trade\t'
                    f'op\t{op + 1}\t'
                    f'cur_time\t{t}\n')

    idxAmtA, idxAmtB, idxzkp11, idxzkp12, idxzkp2, idxzkp3 = reserveInput(web3, appContract, 6, account)
    maskA, maskB, maskzkp11, maskzkp12, maskzkp2, maskzkp3 = get_inputmasks(players(appContract), f'{idxAmtA},{idxAmtB},{idxzkp11},{idxzkp12},{idxzkp2},{idxzkp3}', threshold(appContract))
    maskedAmtA, maskedAmtB, maskedzkp11,maskedzkp12, maskedzkp2, maskedzkp3 = (amtA + maskA) % prime, (amtB + maskB) % prime, (rx + maskzkp11) % prime, (ry + maskzkp12) % prime, (blinding2 + maskzkp2) % prime, (blinding3 + maskzkp3) % prime

    # zkp1 = [idxzkp1, maskedzkp1, proof1, commitment1]
    zkp1 = [idxzkp11, maskedzkp11, idxzkp12, maskedzkp12, Prf1, Cz]
    zkp2 = [idxzkp2, maskedzkp2, proof2, commitment2]
    zkp3 = [idxzkp3, maskedzkp3, proof3, commitment3]
    zkps = json.dumps([zkp1, zkp2, zkp3])

    tx = appContract.functions.trade(tokenA, tokenB, idxAmtA, maskedAmtA, idxAmtB, maskedAmtB, zkps).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    receipt = sign_and_send(tx, web3, account)
    log = appContract.events.Trade().processReceipt(receipt)[0]
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

    web3 = Web3(ws_provider)
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract('hbswap_zkp')
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    account = getAccount(web3, f'/opt/poa/keystore/client_{client_id}/')
    web3.eth.defaultAccount = account.address

    for i in range(repetition):
        trade(appContract, tokenA, tokenB, amtA, amtB, account, web3, client_id)
        time.sleep(10)
        trade(appContract, tokenA, tokenB, amtB, amtA, account, web3, client_id)
        time.sleep(10)
