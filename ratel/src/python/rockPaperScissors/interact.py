ratel/src/python/rockPaperScissors/interact.pyimport asyncio
import time

from web3 import Web3
from web3.middleware import geth_poa_middleware

from ratel.src.python.Client import get_inputmasks, reserveInput
from ratel.src.python.deploy import url, app_addr
from ratel.src.python.utils import parse_contract, getAccount, players, blsPrime, sign_and_send

contract_name = 'rockPaperScissors'

def createGame(appContract, value1, account):
    idx = reserveInput(web3, appContract, 1, account)[0]
    mask = asyncio.run(get_inputmasks(players(appContract), f'{idx}'))[0]
    maskedValue = (value1 + mask) % blsPrime

    web3.eth.defaultAccount = account.address
    tx = appContract.functions.createGame(idx, maskedValue).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    tx_hash = sign_and_send(tx, web3, account)
    receipt = web3.eth.get_transaction_receipt(tx_hash)

    log = appContract.events.CreateGame().processReceipt(receipt)
    gameId = log[0]['args']['gameId']
    while True:
        time.sleep(1)
        status = appContract.functions.status(gameId).call()
        if status == 1:
            return gameId

def joinGame(appContract, gameId, value2, account):
    idx = reserveInput(web3, appContract, 1, account)[0]
    mask = asyncio.run(get_inputmasks(players(appContract), f'{idx}'))[0]
    maskedValue = (value2 + mask) % blsPrime

    web3.eth.defaultAccount = account.address
    tx = appContract.functions.joinGame(gameId, idx, maskedValue).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    tx_hash = sign_and_send(tx, web3, account)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    while True:
        time.sleep(1)
        status = appContract.functions.status(gameId).call()
        if status == 2:
            return

def startRecon(appContract, gameId, account):
    web3.eth.defaultAccount = account.address
    tx = appContract.functions.startRecon(gameId).buildTransaction({
        'nonce': web3.eth.get_transaction_count(web3.eth.defaultAccount)
    })
    tx_hash = sign_and_send(tx, web3, account)
    web3.eth.wait_for_transaction_receipt(tx_hash)

    while True:
        winner = appContract.functions.winners(gameId).call()
        if winner != '':
            print('!!!! winner', winner)
            break
        time.sleep(1)

if __name__=='__main__':
    web3 = Web3(Web3.WebsocketProvider(url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract(contract_name)
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    client_1 = getAccount(web3, f'/opt/poa/keystore/client_1/')
    client_2 = getAccount(web3, f'/opt/poa/keystore/client_2/')

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