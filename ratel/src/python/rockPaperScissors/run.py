import asyncio
import sys
import ratel.genfiles.python.rockPaperScissorsRecover as recover

from ratel.genfiles.python import rockPaperScissors
from ratel.src.python.Server import Server
from ratel.src.python.deploy import app_addr, ws_provider
from ratel.src.python.utils import parse_contract
from web3 import Web3

contract_name = 'rockPaperScissors'

if __name__ == '__main__':
    serverID = int(sys.argv[1])
    init_players = int(sys.argv[2])
    init_threshold = int(sys.argv[3])
    concurrency = int(sys.argv[4])
    test_recover = bool(sys.argv[5])

    web3 = Web3(ws_provider)

    ### App contract
    abi, bytecode = parse_contract(contract_name)
    appContract = web3.eth.contract(address=app_addr, abi=abi)
    ###

    server = Server(
        serverID,
        web3,
        appContract,
        init_players,
        init_threshold,
        concurrency,
        recover,
        test_recover,
    )

    server.loop.run_until_complete(server.init(rockPaperScissors.monitor(server)))