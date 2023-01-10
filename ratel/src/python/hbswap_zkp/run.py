import asyncio
import sys

from ratel.genfiles.python import hbswap_zkp
### recover function
from ratel.genfiles.python.hbswap_zkpRecover import recover
###
from ratel.src.python.Server import Server
from ratel.src.python.deploy import parse_contract, ws_provider, app_addr
from web3 import Web3


contract_name = 'hbswap'


if __name__ == '__main__':
    serverID = int(sys.argv[1])
    init_players = int(sys.argv[2])
    init_threshold = int(sys.argv[3])
    concurrency = int(sys.argv[4])
    test = bool(sys.argv[5])

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
        # test,
    )

    server.loop.run_until_complete(server.init(hbswap_zkp.monitor(server)))
