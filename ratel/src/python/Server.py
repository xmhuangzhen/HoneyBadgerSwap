import json

import aiohttp_cors
import ast
import asyncio
import json
import re
import time

from aiohttp import web, ClientSession
from collections import defaultdict

from ratel.src.python.Client import send_requests, batch_interpolate
from ratel.src.python.utils import key_inputmask_index, threshold_available_input_masks, prime, \
    location_inputmask, http_host, http_port, mpc_port, location_db, openDB, getAccount, \
    confirmation, input_mask_gen_batch_size, list_to_str, trade_key_num, INPUTMASK_SHARES_DIR, execute_cmd, \
    sign_and_send, \
    key_inputmask_version


class Server:
    def __init__(self, serverID, web3, contract, init_players, init_threshold, concurrency, recover):  # , test=False):
        self.serverID = serverID

        self.db = openDB(location_db(serverID))

        self.host = http_host
        self.http_port = http_port + serverID

        self.contract = contract
        self.web3 = web3
        self.account = getAccount(web3, f'/opt/poa/keystore/server_{serverID}/')

        self.confirmation = confirmation

        self.players = init_players
        self.threshold = init_threshold

        self.concurrency = concurrency

        self.portLock = {}
        for i in range(-1, concurrency):
            self.portLock[mpc_port + i * 100] = asyncio.Lock()

        self.dbLock = {}
        self.dbLockCnt = {}

        self.loop = asyncio.get_event_loop()

        self.zkrpShares = {}

        self.input_mask_cache = []
        self.input_mask_version = 0

        # self.recover = recover

        # self.test = test
        #
        # self.input_mask_queue_tail = 0
        # try:
        #     self.input_mask_queue_tail = int.from_bytes(bytes(self.db.Get(f'input_mask_queue_tail'.encode())), 'big')
        # except KeyError:
        #     pass
        # print('**** input_mask_queue_tail', self.input_mask_queue_tail)

    async def get_zkrp_shares(self, players, inputmask_idxes):
        request = f"zkrp_share_idxes/{inputmask_idxes}"
        results = await send_requests(players, request)
        parsed_results = []
        for i in range(len(results)):
            parsed_results.append(json.loads(results[i]["zkrp_share_idx"]))

        return parsed_results

    async def http_server(self):
        async def handler_inputmask(request):
            print(f"s{self.serverID} request: {request}")
            mask_idxes = re.split(",", request.match_info.get("mask_idxes"))
            res = ""
            for mask_idx in mask_idxes:
                res += f"{',' if len(res) > 0 else ''}{int.from_bytes(bytes(self.db.Get(key_inputmask_index(mask_idx))), 'big')}"
            data = {
                "inputmask_shares": res,
            }
            print(f"s{self.serverID} response: {res}")
            return web.json_response(data)

        # async def handler_recover_db(request):
        #     print(f"s{self.serverID} request: {request}")
        #     seq_num_list = re.split(',', request.match_info.get("list"))
        #
        #     with open(f'ratel/benchmark/data/recover_states.csv', 'a') as f:
        #         f.write(f'state\t{len(seq_num_list * trade_key_num)}\t'
        #                 f'stage\t3\t'
        #                 f'{time.perf_counter()}\t'
        #                 f's-{self.serverID}\n')
        #
        #     keys = self.collect_keys(seq_num_list)
        #     masked_shares = await self.mask_shares(keys)
        #
        #     with open(f'ratel/benchmark/data/recover_states.csv', 'a') as f:
        #         f.write(f'state\t{len(seq_num_list * trade_key_num)}\t'
        #                 f'stage\t6\t'
        #                 f'{time.perf_counter()}\t'
        #                 f's-{self.serverID}\n')
        #
        #     res = list_to_str(masked_shares)
        #
        #     data = {
        #         "values": res,
        #     }
        #     print(f"s{self.serverID} response: {res}")
        #     return web.json_response(data)

        async def handler_mpc_verify(request):
            print(f"s{self.serverID} request: s{request} request from {request.remote}")
            mask_idx = re.split(',', request.match_info.get("mask_idxes"))[0]

            while mask_idx not in self.zkrpShares.keys():
                await asyncio.sleep(1)

            data = {
                "zkrp_share_idx": json.dumps(self.zkrpShares[mask_idx]),
            }
            return web.json_response(data)

        app = web.Application()

        cors = aiohttp_cors.setup(
            app,
            defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                )
            },
        )

        resource = cors.add(app.router.add_resource("/inputmasks/{mask_idxes}"))
        cors.add(resource.add_route("GET", handler_inputmask))
        # resource = cors.add(app.router.add_resource("/recoverdb/{list}"))
        # cors.add(resource.add_route("GET", handler_recover_db))
        resource = cors.add(app.router.add_resource("/zkrp_share_idxes/{mask_idxes}"))
        cors.add(resource.add_route("GET", handler_mpc_verify))

        print("Starting http server...")
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.host, port=self.http_port)
        await site.start()
        await asyncio.sleep(100 * 3600)

    # TODO: modify the following
    # async def init(self, apptask):
    #     async def prepare(apptask):
    #         # isServer = self.contract.functions.isServer(self.account.address).call()
    #         # if not isServer:
    #         #     self.registerServer()
    #         #     await self.recoverHistory()
    #
    #         tasks = [
    #             self.preprocessing(),
    #             # self.monitorNewServer(),
    #             self.http_server(),
    #             apptask,
    #         ]
    #         await asyncio.gather(*tasks)
    #
    #     tasks = [
    #         prepare(apptask),
    #         self.monitorGenInputMask(shareBatchSize),
    #     ]
    #     await asyncio.gather(*tasks)

    async def init(self, monitor):
        # TODO: consider where the recover_history function should be invoked
        await self.recover_history()

        tasks = [
            monitor,
            self.http_server(),
            self.preprocessing()
        ]
        await asyncio.gather(*tasks)

    async def request_state_mask(self, num):
        tx = self.contract.functions.genStateMask(num).buildTransaction(
            {'from': self.account.address, 'gas': 1000000,
             'nonce': self.web3.eth.get_transaction_count(self.account.address)})
        sign_and_send(tx, self.web3, self.account)

    async def gen_random_field_elements(self, batch_size=input_mask_gen_batch_size):
        print(f'Generating new inputmasks... s-{self.serverID}')

        cmd = f'./random-shamir.x -i {self.serverID} -N {self.players} -T {self.threshold} --nshares {batch_size} --prep-dir {INPUTMASK_SHARES_DIR} -P {prime}'
        await execute_cmd(cmd)

        file = location_inputmask(self.serverID, self.players)
        shares = []
        with open(file, "r") as f:
            for line in f.readlines():
                share = int(line) % prime
                shares.append(share)

        return shares

    # async def gen_input_mask(self, input_mask_cnt, input_mask_version, share_batch_size=shareBatchSize):
    #     print(f'Generating new inputmasks... s-{self.serverID}')
    #
    #     cmd = f'./random-shamir.x -i {self.serverID} -N {self.players} -T {self.threshold} --nshares {share_batch_size} --prep-dir {INPUTMASK_SHARES_DIR} -P {prime}'
    #     await execute_cmd(cmd)
    #
    #     file = location_inputmask(self.serverID, self.players)
    #     with open(file, "r") as f:
    #         for line in f.readlines():
    #             share = int(line) % prime
    #             self.db.Put(key_inputmask_index(input_mask_cnt), share.to_bytes((share.bit_length() + 7) // 8, 'big'))
    #             self.db.Put(key_inputmask_version(input_mask_cnt), input_mask_version.to_bytes((input_mask_version.bit_length() + 7) // 8, 'big'))
    #             input_mask_cnt += 1
    #
    #     # self.db.Put(f'input_mask_queue_tail'.encode(), self.input_mask_queue_tail.to_bytes((self.input_mask_queue_tail.bit_length() + 7) // 8, 'big'))
    #
    #     self.local_input_mask_cnt = input_mask_cnt
    #     print(f'Total inputmask number: {self.local_input_mask_cnt}\n')

    # async def check_input_mask_availability(self):
    #     input_mask_queue_head = self.contract.functions.inputMaskCnt().call()
    #     if input_mask_queue_head + spareShares >= self.input_mask_queue_tail:
    #         await self.genInputMask(shareBatchSize)

    async def preprocessing(self):
        ### TODO: remove the following & add generating agreement proof
        if self.serverID != 0:
            return

        while True:
            num_used_input_mask = self.contract.functions.numUsedInputMask().call()
            num_total_input_mask = self.contract.functions.numTotalInputMask().call()
            if num_used_input_mask - num_used_input_mask < threshold_available_input_masks:
                print(f'Initialize input mask generation process....')
                tx = self.contract.functions.initGenInputMask(True).buildTransaction(
                    {'from': self.account.address, 'gas': 1000000,
                     'nonce': self.web3.eth.get_transaction_count(self.account.address)})
                sign_and_send(tx, self.web3, self.account)
            await asyncio.sleep(600)

        # while True:
        #     input_mask_cnt = self.contract.functions.inputMaskCnt().call()
        #     if input_mask_cnt + spareShares >= self.local_input_mask_cnt:
        #         print(f'Request to generate input masks....')
        #         tx = self.contract.functions.genInputMask(self.local_input_mask_cnt).buildTransaction(
        #             {'from': self.account.address, 'gas': 1000000,
        #              'nonce': self.web3.eth.get_transaction_count(self.account.address)})
        #         sign_and_send(tx, self.web3, self.account)
        #     await asyncio.sleep(600)

        # while True:
        #     if self.contract.functions.isInputMaskReady().call() > self.contract.functions.T().call() and self.contract.functions.isServer(self.account.address).call():
        #         await self.check_input_mask_availability()
        #     await asyncio.sleep(60)

    # async def monitorGenInputMask(self, shareBatchSize):
    #     blkNum = self.web3.eth.get_block_number()
    #     while True:
    #         await asyncio.sleep(5)
    #         curBlkNum = self.web3.eth.get_block_number()
    #         if curBlkNum - blkNum > self.confirmation:
    #             eventFilter = self.contract.events.GenInputMask.createFilter(fromBlock=blkNum, toBlock=curBlkNum - self.confirmation)
    #             logs = eventFilter.get_all_entries()
    #             blkNum = curBlkNum - self.confirmation + 1
    #             for log in logs:
    #                 input_mask_queue_head = log['args']['inputMaskCnt']
    #                 committeeChangeCnt = log['args']['committeeChangeCnt']
    #
    #                 self.input_mask_queue_tail = input_mask_queue_head
    #                 await self.genInputMask(shareBatchSize)
    #
    #                 tx = self.contract.functions.setReady(committeeChangeCnt).buildTransaction({'from': self.account.address, 'gas': 1000000, 'nonce': self.web3.eth.get_transaction_count(self.account.address)})
    #                 sign_and_send(tx, self.web3, self.account)
    #                 print('!!!! isInputMaskReady', self.contract.functions.isInputMaskReady().call())
    #
    #
    # async def monitorNewServer(self):
    #     blkNum = self.web3.eth.get_block_number()
    #     while True:
    #         await asyncio.sleep(5)
    #         curBlkNum = self.web3.eth.get_block_number()
    #         if curBlkNum - blkNum > self.confirmation:
    #             eventFilter = self.contract.events.NewServer.createFilter(fromBlock=blkNum, toBlock=curBlkNum - self.confirmation)
    #             logs = eventFilter.get_all_entries()
    #             blkNum = curBlkNum - self.confirmation + 1
    #             for log in logs:
    #                 newServer = log['args']['server']
    #
    #                 self.players += 1
    #
    #                 tx = self.contract.functions.addServer(newServer).buildTransaction({'from': self.account.address, 'gas': 1000000, 'nonce': self.web3.eth.get_transaction_count(self.account.address)})
    #                 sign_and_send(tx, self.web3, self.account)
    #                 print('!!!! votes', self.contract.functions.votes(newServer).call())
    #
    # def registerServer(self):
    #     tx = self.contract.functions.registerServer().buildTransaction({'from': self.account.address, 'gas': 1000000, 'nonce': self.web3.eth.get_transaction_count(self.account.address)})
    #     sign_and_send(tx, self.web3, self.account)
    #
    #
    async def recover_history(self):
        self.check_missing_tasks()

    #     while True:
    #         isServer = self.contract.functions.isServer(self.account.address).call()
    #         print('isServer', isServer)
    #         if isServer:
    #             break
    #         await asyncio.sleep(1)
    #     while True:
    #         committeeChangeCnt = self.contract.functions.committeeChangeCnt().call()
    #         numCommittee = self.contract.functions.numCommittee(self.account.address).call()
    #         print('committeeChangeCnt', committeeChangeCnt, 'numCommittee', numCommittee)
    #         if numCommittee == committeeChangeCnt:
    #             break
    #         await asyncio.sleep(1)
    #
    #     #TODO: test below
    #     seq_num_list = self.check_missing_tasks()
    #     request = f'recoverdb/{list_to_str(seq_num_list)}'
    #     masked_shares = await send_requests(self.players, request)
    #     for i in range(len(masked_shares)):
    #         masked_shares[i] = re.split(",", masked_shares[i]["values"])
    #     keys = self.collect_keys(seq_num_list)
    #     masked_states = batch_interpolate(masked_shares)
    #     state_shares = self.recover_states(masked_states)
    #     self.restore_db(seq_num_list, keys, state_shares)
    #
    #
    def check_missing_tasks(self):
        try:
            exec_history = self.db.Get(f'execHistory'.encode())
        except KeyError:
            exec_history = bytes(0)

        try:
            exec_history = exec_history.decode(encoding='utf-8')
            exec_history = dict(ast.literal_eval(exec_history))
        except:
            exec_history = {}

        finalized_task_cnt = self.contract.functions.finalizedTaskCnt().call()
        print(f'finalized_task_cnt {finalized_task_cnt}')
        for finalized_seq in range(1, 1 + finalized_task_cnt):
            if not finalized_seq in exec_history:
                init_seq = self.contract.functions.finalized(finalized_seq).call()
                print(f'missing task with initSeq {init_seq} finalizedSeq {finalized_seq}')

        # TODO: recover states of on-going MPC tasks

        # opCnt = self.contract.functions.opCnt().call()
        # seq_num_list = []
        # for seq in range(opCnt):
        #     if not seq in exec_history:
        #         print('missing opSeq', seq)
        #         seq_num_list.append(seq)
        # return seq_num_list
    #
    #
    # def collect_keys(self, seq_num_list):
    #     if not self.test:
    #         seq_num_list = list(set(seq_num_list))
    #
    #     keys = []
    #     for seq_num in seq_num_list:
    #         keys.extend(self.recover(self.contract, int(seq_num)))
    #
    #     if not self.test:
    #         keys = list(set(keys))
    #
    #     return keys
    #
    #
    # async def mask_shares(self, keys):
    #     masked_shares = []
    #
    #     with open(f'ratel/benchmark/data/recover_states.csv', 'a') as f:
    #         f.write(f'state\t{len(keys)}\t'
    #                 f'stage\t4\t'
    #                 f'{time.perf_counter()}\t'
    #                 f's-{self.serverID}\n')
    #
    #     await self.genInputMask(len(keys))
    #
    #     with open(f'ratel/benchmark/data/recover_states.csv', 'a') as f:
    #         f.write(f'state\t{len(keys)}\t'
    #                 f'stage\t5\t'
    #                 f'{time.perf_counter()}\t'
    #                 f's-{self.serverID}\n')
    #
    #     for key in keys:
    #         masked_state_share = 0
    #         try:
    #             secret = int.from_bytes(bytes(self.db.Get(key.lower().encode())), 'big')
    #
    #             input_mask_share = int.from_bytes(bytes(self.db.Get(key_inputmask_index(self.input_mask_queue_tail - 1))), 'big')
    #             self.input_mask_queue_tail -= 1
    #             masked_state_share = (secret + input_mask_share) % prime
    #
    #         except KeyError:
    #             print(f'Do not have the state {key}')
    #
    #         masked_shares.append(masked_state_share)
    #
    #     self.db.Put(f'input_mask_queue_tail'.encode(), self.input_mask_queue_tail.to_bytes((self.input_mask_queue_tail.bit_length() + 7) // 8, 'big'))
    #
    #     return masked_shares
    #
    #
    # def recover_states(self, masked_states):
    #     state_shares = []
    #
    #     for masked_state in masked_states:
    #         input_mask = int.from_bytes(bytes(self.db.Get(key_inputmask_index(self.input_mask_queue_tail - 1))), 'big')
    #         self.input_mask_queue_tail -= 1
    #         state_share = (masked_state - input_mask) % prime
    #         state_shares.append(state_share)
    #
    #     self.db.Put(f'input_mask_queue_tail'.encode(), self.input_mask_queue_tail.to_bytes((self.input_mask_queue_tail.bit_length() + 7) // 8, 'big'))
    #
    #     return state_shares
    #
    #
    # def restore_db(self, seq_num_list, keys, values):
    #     assert len(keys) == len(values)
    #
    #     for key, value in zip(keys, values):
    #         self.db.Put(key.encode(), value.to_bytes((value.bit_length() + 7) // 8, 'big'))
    #
    #     try:
    #         execHistory = self.db.Get(f'execHistory'.encode())
    #     except KeyError:
    #         execHistory = bytes(0)
    #
    #     try:
    #         execHistory = execHistory.decode(encoding='utf-8')
    #         execHistory = dict(ast.literal_eval(execHistory))
    #     except:
    #         execHistory = {}
    #
    #     for seq in seq_num_list:
    #             execHistory[seq] = True
    #
    #     execHistory = str(execHistory)
    #     execHistory = bytes(execHistory, encoding='utf-8')
    #     self.db.Put(f'execHistory'.encode(), execHistory)
