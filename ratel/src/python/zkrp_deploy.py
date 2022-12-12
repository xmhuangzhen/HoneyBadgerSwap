import sys

from web3 import Web3
from ratel.src.python.utils import getAccount, parse_contract
from ratel.src.python.deploy import url, app_addr
from ratel.src.python.Server import Server
from ratel.src.python.utils import parse_contract, repeat_experiment
from ratel.genfiles.python.rockPaperScissorsRecover import recover


if __name__=='__main__':
    appName = sys.argv[1]
    init_players = int(sys.argv[2])
    init_threshold = int(sys.argv[3])
    concurrency = int(sys.argv[4])

    with open('ratel/genfiles/tmp.txt', 'r') as f:
        sum_zkrp = int(f.read())
    # print('sum_zkrp',sum_zkrp)

    web3 = Web3(Web3.WebsocketProvider(url))
    abi, bytecode = parse_contract(appName)
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    for serverID in range(init_players):
        server = Server(
            serverID,
            web3,
            appContract,
            init_players,
            init_threshold,
            concurrency,
            recover,
            # 0
        )
        server.gen_

