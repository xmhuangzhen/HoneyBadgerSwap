import asyncio
import aio_eth
import time

from web3 import Web3
from eth_abi import decode_single

from ratel.src.python.deploy import http_uri, app_addr, ws_provider
from ratel.src.python.utils import parse_contract, getAccount
from hexbytes import HexBytes
import eth_abi


async def query_blocks():

    web3 = Web3(ws_provider)

    ### App contract
    contract_name = 'rockPaperScissors'
    abi, bytecode = parse_contract(contract_name)
    contract = web3.eth.contract(address=app_addr, abi=abi)
    ###

    client = getAccount(web3, f'/opt/poa/keystore/client_1/')

    # create the API handle
    async with aio_eth.EthAioAPI(http_uri, max_tasks=100) as api:
        # express queries - example: get all transactions from 70 blocks
        # starting from 10553978
        for i in range(0, 100):
            # data = contract.encodeABI(fn_name='opEvent', args=[1])
            data = contract.encodeABI(fn_name='opContent', args=[1])
            # data = contract.encodeABI(fn_name='gamePlayer1', args=[1])
            # data = contract.encodeABI(fn_name='gameCnt', args=[])
            # print(data)

            # submit tasks to the task list, if `current tasks > max_tasks`
            # this method throws an exception.
            api.push_task({
                "method": "eth_call",
                "params": [
                    {
                        # "from": client.address,
                        "to": app_addr,
                        "data": data,
                    },
                    "latest"
                ]
            })

        st = time.time()
        # execute the tasks together as batch, outputs are returned in the same
        # order in which their corresponding queries where submitted.
        results = await api.exec_tasks_batch()
        for result in results:
            print(result)
            print(result['result'])
            print(HexBytes(result['result']))
            # print(eth_abi.decode_abi(['string'], HexBytes(result['result'])))
            res = eth_abi.decode_abi(['bytes'], HexBytes(result['result']))[0]
            print(res)
            print(decode_single('(uint,address,uint,uint,uint,uint,uint8[],uint8[])', res))
            # log = appContract.events.NewTruck().processReceipt(receipt)
            break

        et = time.time()
        print('time taken: ', et - st, ' seconds')


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(query_blocks())
