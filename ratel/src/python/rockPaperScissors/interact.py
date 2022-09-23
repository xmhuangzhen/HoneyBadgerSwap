import asyncio
import time


from web3 import Web3
from web3.middleware import geth_poa_middleware

from ratel.src.python.Client import get_inputmasks, reserveInput
from ratel.src.python.deploy import url, app_addr
from ratel.src.python.utils import (
    parse_contract,
    getAccount,
    players,
    prime,
    sign_and_send,
    threshold,
    get_zkrp,
)

from pybulletproofs import zkrp_prove


contract_name = "rockPaperScissors"


def createGame(appContract, value1, account):
    print(f'**** CreateGame {value1}')

    zkp_value1, proof1, commitment1, blinding1 = get_zkrp(value1, '>=', 1)
    zkp_value2, proof2, commitment2, blinding2 = get_zkrp(value1, '<=', 100)

    idx1, idx2, idx3, idx4, idx5 = reserveInput(web3, appContract, 5, account)
    mask1, mask2, mask3, mask4, mask5 = asyncio.run(get_inputmasks(players(appContract), f'{idx1},{idx2},{idx3},{idx4},{idx5}', threshold(appContract)))
    maskedvalue1, maskedvalue2, maskedvalue3, maskedvalue4, maskedvalue5 = (value1 + mask1) % prime, (zkp_value1 + mask2) % prime, (blinding1 + mask3) % prime, (zkp_value2 + mask4) % prime, (blinding2 + mask5) % prime

    web3.eth.defaultAccount = account.address
    tx = appContract.functions.createGame(idx1, maskedvalue1, idx2, maskedvalue2, idx3, maskedvalue3, proof1, commitment1, idx4, maskedvalue4, idx5, maskedvalue5, proof2, commitment2).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    receipt = sign_and_send(tx, web3, account)

    log = appContract.events.CreateGame().processReceipt(receipt)
    gameId = log[0]["args"]["gameId"]
    while True:
        time.sleep(1)
        status = appContract.functions.status(gameId).call()
        if status == 1:
            return gameId


def joinGame(appContract, gameId, value2, account):
    print(f'**** JoinGame {value2}')
    idx = reserveInput(web3, appContract, 1, account)[0]
    mask = asyncio.run(
        get_inputmasks(players(appContract), f"{idx}", threshold(appContract))
    )[0]
    maskedValue = (value2 + mask) % prime

    web3.eth.defaultAccount = account.address
    tx = appContract.functions.joinGame(gameId, idx, maskedValue).buildTransaction(
        {"nonce": web3.eth.get_transaction_count(web3.eth.defaultAccount)}
    )
    sign_and_send(tx, web3, account)

    while True:
        time.sleep(1)
        status = appContract.functions.status(gameId).call()
        if status == 2:
            return


def startRecon(appContract, gameId, account):
    web3.eth.defaultAccount = account.address
    tx = appContract.functions.startRecon(gameId).buildTransaction(
        {"nonce": web3.eth.get_transaction_count(web3.eth.defaultAccount)}
    )
    sign_and_send(tx, web3, account)

    while True:
        winner = appContract.functions.winners(gameId).call()
        if winner != "":
            print("!!!! winner", winner)
            break
        time.sleep(1)


if __name__ == "__main__":
    web3 = Web3(Web3.WebsocketProvider(url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract(contract_name)
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    client_1 = getAccount(web3, f"/opt/poa/keystore/client_1/")
    client_2 = getAccount(web3, f"/opt/poa/keystore/client_2/")

    gameId = createGame(appContract, 1, client_1)
    joinGame(appContract, gameId, 1, client_2)
    startRecon(appContract, gameId, client_1)

    gameId = createGame(appContract, 1, client_1)
    joinGame(appContract, gameId, 2, client_2)
    startRecon(appContract, gameId, client_2)

    gameId = createGame(appContract, 1, client_1)
    joinGame(appContract, gameId, 3, client_2)
    startRecon(appContract, gameId, client_1)

    gameId = createGame(appContract, 2, client_1)
    joinGame(appContract, gameId, 1, client_2)
    startRecon(appContract, gameId, client_1)

    gameId = createGame(appContract, 2, client_1)
    joinGame(appContract, gameId, 2, client_2)
    startRecon(appContract, gameId, client_1)

    gameId = createGame(appContract, 2, client_1)
    joinGame(appContract, gameId, 3, client_2)
    startRecon(appContract, gameId, client_1)

    gameId = createGame(appContract, 3, client_1)
    joinGame(appContract, gameId, 1, client_2)
    startRecon(appContract, gameId, client_1)

    gameId = createGame(appContract, 3, client_1)
    joinGame(appContract, gameId, 2, client_2)
    startRecon(appContract, gameId, client_1)

    gameId = createGame(appContract, 3, client_1)
    joinGame(appContract, gameId, 3, client_2)
    startRecon(appContract, gameId, client_1)
