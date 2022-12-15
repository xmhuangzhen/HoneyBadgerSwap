import sys

from ratel.src.python.rockPaperScissors.integration_test import http_uri, app_addr, contract_name, createGame, \
    parse_contract, getAccount, geth_poa_middleware, Web3

if __name__ == "__main__":
    client_id = int(sys.argv[1])
    print(f'client_{client_id}')
    value = int(sys.argv[2])

    web3 = Web3(Web3.HTTPProvider(http_uri))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract(contract_name)
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    client = getAccount(web3, f'/opt/poa/keystore/client_{client_id}/')

    game_id = createGame(appContract, value, client, web3)
    print(f'game_id {game_id}')
