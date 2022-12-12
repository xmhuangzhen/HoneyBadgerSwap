import asyncio
import sys

from ratel.genfiles.python.rockPaperScissors import monitor
from ratel.genfiles.python.rockPaperScissorsRecover import recover
from ratel.src.python.Server import Server
from ratel.src.python.deploy import url, app_addr
from ratel.src.python.rockPaperScissors.integration_test import geth_poa_middleware
from ratel.src.python.utils import parse_contract, sign_and_send
from web3 import Web3


def get_next_argv():
    cnt[0] += 1
    return sys.argv[cnt[0]]


async def test():
    await server.prepare(repetition)

    tx = server.contract.functions.removeServer(server.account.address).buildTransaction({
        'from': server.account.address,
        'gas': 1000000,
        'nonce': server.web3.eth.get_transaction_count(server.account.address)
    })
    sign_and_send(tx, server.web3, server.account)


async def server_job():
    tasks = [
        monitor(server),
        test(),
    ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    cnt = [0]
    serverID = int(get_next_argv())
    online_players = int(get_next_argv())
    init_threshold = int(get_next_argv())
    concurrency = int(get_next_argv())
    repetition = int(get_next_argv())

    web3 = Web3(Web3.WebsocketProvider(url))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi, bytecode = parse_contract('rockPaperScissors')
    appContract = web3.eth.contract(address=app_addr, abi=abi)

    server = Server(
        serverID,
        web3,
        appContract,
        online_players,
        init_threshold,
        concurrency,
        recover,
        test_recover=True,
    )

    server.loop.run_until_complete(server_job())
