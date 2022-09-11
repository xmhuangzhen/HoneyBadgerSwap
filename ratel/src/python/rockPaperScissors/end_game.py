import sys

from ratel.src.python.rockPaperScissors.integration_test import url, app_addr, contract_name, joinGame, \
    parse_contract, getAccount, geth_poa_middleware, Web3, startRecon

if __name__ == "__main__":
    client_id = int(sys.argv[1])
    print(f'client_{client_id}')
    value = int(sys.argv[2])
    game_id = int(sys.argv[3])

    web3 = Web3(Web3.WebsocketProvider(url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract(contract_name)
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    client = getAccount(web3, f'/opt/poa/keystore/client_{client_id}/')

    joinGame(appContract, game_id, value, client, web3)
    startRecon(appContract, game_id, client, web3)
