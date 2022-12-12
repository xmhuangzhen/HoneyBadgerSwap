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
    key_inputmask_version, key_state_mask, read_db, bytes_to_dict, dict_to_bytes, write_db


class Server:
    def __init__(self, serverID, web3, contract, init_players, init_threshold, concurrency, recover , test_recover=False):
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

        self.recover = recover

        self.test_recover = test_recover

    async def get_zkrp_shares(self, players, inputmask_idxes):
        request = f"zkrp_share_idxes/{inputmask_idxes}"
        results = await send_requests(players, request)
        shares = []
        server_indexes = []
        for i in range(len(results)):
            if len(results[i]):
                shares.append(json.loads(results[i]["zkrp_share_idx"]))
                server_indexes.append(i + 1)

        return shares, server_indexes

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

        async def handler_recover_db(request):
            print(f"s{self.serverID} request: {request}")
            server_addr = request.match_info.get("server_addr")
            seq_recover_state = int(request.match_info.get("seq_recover_state"))
            seq_num_list = re.split(',', request.match_info.get("list"))
            print(server_addr)
            print(seq_recover_state)
            print(seq_num_list)

            keys = self.collect_keys(seq_num_list)
            masked_states = await self.mask_states(server_addr, seq_recover_state, keys)

            res = list_to_str(masked_states)

            data = {
                "values": res,
            }
            print(f"s{self.serverID} response: {res}")
            return web.json_response(data)

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
        resource = cors.add(app.router.add_resource("/recoverdb/{server_addr}-{seq_recover_state}-{list}"))
        cors.add(resource.add_route("GET", handler_recover_db))
        resource = cors.add(app.router.add_resource("/zkrp_share_idxes/{mask_idxes}"))
        cors.add(resource.add_route("GET", handler_mpc_verify))

        print("Starting http server...")
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=self.host, port=self.http_port)
        await site.start()
        await asyncio.sleep(100 * 3600)

    async def init(self, monitor):
        tasks = [
            self.prepare(),
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
        print(f'Generating {batch_size} random field elements... s-{self.serverID}')

        cmd = f'./random-shamir.x -i {self.serverID} -N {self.players} -T {self.threshold} --nshares {batch_size} --prep-dir {INPUTMASK_SHARES_DIR} -P {prime}'
        await execute_cmd(cmd)

        file = location_inputmask(self.serverID, self.players)
        shares = []
        with open(file, "r") as f:
            for line in f.readlines():
                share = int(line) % prime
                shares.append(share)
        return shares

    async def preprocessing(self):
        # TODO: remove the following & add generating agreement proof
        if self.serverID != 0:
            return

        while True:
            num_used_input_mask = self.contract.functions.numUsedInputMask().call()
            num_total_input_mask = self.contract.functions.numTotalInputMask().call()
            if num_total_input_mask - num_used_input_mask < threshold_available_input_masks:
                print(f'Initialize input mask generation process....')
                tx = self.contract.functions.initGenInputMask(True).buildTransaction(
                    {'from': self.account.address, 'gas': 1000000,
                     'nonce': self.web3.eth.get_transaction_count(self.account.address)})
                sign_and_send(tx, self.web3, self.account)
            await asyncio.sleep(600)

    async def prepare(self, repetition=1):
        # TODO: consider the ordering of crash recovery related functions
        is_server = self.contract.functions.isServer(self.account.address).call()
        print(f's-{self.serverID} {is_server}')
        if not is_server:
            # TODO: acquire approval from other servers
            tx = self.contract.functions.addServer(self.account.address).buildTransaction({
                'from': self.account.address,
                'gas': 1000000,
                'nonce': self.web3.eth.get_transaction_count(self.account.address)
            })
            sign_and_send(tx, self.web3, self.account)
        if not self.test_recover:
            await self.check_input_mask()

        seq_num_list = self.check_missing_tasks() * repetition
        print(f'seq_num_list {seq_num_list}')
        if len(seq_num_list) == 0:
            return
        await self.recover_history(seq_num_list, repetition)

    async def check_input_mask(self):
        version_input_mask = self.contract.functions.versionInputMask().call()
        num_total_input_mask = self.contract.functions.numTotalInputMask().call()
        print(f'version_input_mask {version_input_mask}')
        print(f'num_total_input_mask {num_total_input_mask}')

        out_of_date = False
        try:
            local_version = int.from_bytes(bytes(self.db.Get(key_inputmask_version(num_total_input_mask - 1))), 'big')
            if local_version < version_input_mask:
                out_of_date = True
        except KeyError:
            out_of_date = True

        if out_of_date:
            tx = self.contract.functions.initGenInputMask(True).buildTransaction({
                'from': self.account.address,
                'gas': 1000000,
                'nonce': self.web3.eth.get_transaction_count(self.account.address)
            })
            sign_and_send(tx, self.web3, self.account)

            while True:
                try:
                    print(f'idx {num_total_input_mask - 1}')
                    local_version = int.from_bytes(bytes(self.db.Get(key_inputmask_version(num_total_input_mask - 1))), 'big')
                    print(f'local_version {local_version}')
                    if local_version > version_input_mask:
                        break
                except:
                    pass
                await asyncio.sleep(1)

    async def recover_history(self, seq_num_list, repetition):
        ### benchmark
        times = []
        times.append(time.perf_counter())

        keys = self.collect_keys(seq_num_list)
        # print(f'keys {keys}')

        ### benchmark
        times.append(time.perf_counter())

        seq_recover_state = await self.reserve_state_mask(len(keys))

        ### benchmark
        times.append(time.perf_counter())

        request = f'recoverdb/{self.account.address}-{seq_recover_state}-{list_to_str(seq_num_list)}'
        # print(request)

        masked_states = await send_requests(self.players, request, self.serverID)

        ### benchmark
        times.append(time.perf_counter())

        batch_points = []
        for i in range(len(masked_states)):
            if len(masked_states[i]):
                batch_points.append((i + 1, re.split(",", masked_states[i]["values"])))
        masked_states = batch_interpolate(self.serverID + 1, batch_points, self.threshold)
        state_shares = self.unmask_states(masked_states, seq_recover_state)

        ### benchmark
        times.append(time.perf_counter())

        self.restore_db(seq_num_list, keys, state_shares)

        ### benchmark
        times.append(time.perf_counter())

        ### benchmark
        with open(f'ratel/benchmark/data/recover_states_{repetition}.csv', 'a') as f:
            for op, t in enumerate(times):
                f.write(f'op\t{op + 1}\t'
                        f'cur_time\t{t}\n')

        # TODO: recover states of on-going MPC tasks

    def check_missing_tasks(self):
        key = 'execHistory'
        exec_history = read_db(self, key)
        exec_history = bytes_to_dict(exec_history)

        seq_list = []

        finalized_task_cnt = self.contract.functions.finalizedTaskCnt().call()
        print(f'finalized_task_cnt {finalized_task_cnt}')
        for finalized_seq in range(1, 1 + finalized_task_cnt):
            if finalized_seq not in exec_history or not exec_history[finalized_seq]:
                init_seq = self.contract.functions.finalized(finalized_seq).call()
                print(f'missing task with initSeq {init_seq} finalizedSeq {finalized_seq}')
                seq_list.append(init_seq)

        return seq_list

    def collect_keys(self, seq_num_list):
        if not self.test_recover:
            seq_num_list = list(set(seq_num_list))

        keys = []
        for seq_num in seq_num_list:
            keys.extend(self.recover(self.contract, int(seq_num), 'writeSet'))

        if not self.test_recover:
            keys = list(set(keys))

        return keys

    async def reserve_state_mask(self, num):
        print('reserve_state_mask')
        num_total_state_mask = self.contract.functions.numTotalStateMask(self.account.address).call()
        num_used_state_mask = self.contract.functions.numUsedStateMask(self.account.address).call()
        num_to_gen = max(0, num - num_total_state_mask + num_used_state_mask)
        print(f'num_to_gen {num_to_gen}')

        if num_to_gen > 0:
            print(f'generating {num_to_gen} state masks...')
            tx = self.contract.functions.genStateMask(num_to_gen).buildTransaction({
                'from': self.account.address,
                'gas': 1000000,
                'nonce': self.web3.eth.get_transaction_count(self.account.address)
            })
            receipt = sign_and_send(tx, self.web3, self.account)
            logs = self.contract.events.GenStateMask().processReceipt(receipt)
            init_state_mask_index = logs[0]['args']['initStateMaskIndex']
            num = logs[0]['args']['num']

            print(f'init_state_mask_index {init_state_mask_index}')
            print(f'num {num}')

            while True:
                try:
                    self.db.Get(key_state_mask(self.account.address, init_state_mask_index + num - 1))
                    break
                except KeyError:
                    print(f'state mask generation not ready')
                    await asyncio.sleep(1)

        tx = self.contract.functions.consumeStateMask(num).buildTransaction({
            'from': self.account.address,
            'gas': 1000000,
            'nonce': self.web3.eth.get_transaction_count(self.account.address)
        })
        receipt = sign_and_send(tx, self.web3, self.account)
        logs = self.contract.events.RecoverState().processReceipt(receipt)
        seq_recover_state = logs[0]['args']['seqRecoverState']

        return seq_recover_state

    async def mask_states(self, server_addr, seq_recover_state, keys):
        # TODO: deal with the case that malicious MPC server reuse the same seq_num
        # TODO: handle the case when the server does not have the share of some state masks

        masked_states = []

        init_index_recover_state = self.contract.functions.initIndexRecoverState(server_addr, seq_recover_state).call()
        num_recover_state = self.contract.functions.numRecoverState(server_addr, seq_recover_state).call()

        if num_recover_state != len(keys):
            print(f'invalid recover state request')
            return masked_states

        for idx, key in zip(range(init_index_recover_state, init_index_recover_state + num_recover_state), keys):
            state = int.from_bytes(bytes(self.db.Get(key.lower().encode())), 'big')
            state_mask_share = int.from_bytes(bytes(self.db.Get(key_state_mask(server_addr, idx))), 'big')
            masked_state_share = (state + state_mask_share) % prime
            masked_states.append(masked_state_share)

        return masked_states

    def unmask_states(self, masked_states, seq_recover_state):
        state_shares = []

        init_index_recover_state = self.contract.functions.initIndexRecoverState(self.account.address, seq_recover_state).call()
        num_recover_state = self.contract.functions.numRecoverState(self.account.address, seq_recover_state).call()

        for idx, masked_state in zip(range(init_index_recover_state, init_index_recover_state + num_recover_state), masked_states):
            state_mask_share = int.from_bytes(bytes(self.db.Get(key_state_mask(self.account.address, idx))), 'big')
            state_share = (masked_state - state_mask_share) % prime
            state_shares.append(state_share)

        return state_shares

    def restore_db(self, seq_num_list, keys, values):
        assert len(keys) == len(values)

        for key, value in zip(keys, values):
            # print(f'key {key} value {value}')
            self.db.Put(key.encode(), value.to_bytes((value.bit_length() + 7) // 8, 'big'))

        key = 'execHistory'
        exec_history = read_db(self, key)
        exec_history = bytes_to_dict(exec_history)

        for seq in seq_num_list:
            exec_history[seq] = True

        exec_history = dict_to_bytes(exec_history)
        write_db(self, key, exec_history)
