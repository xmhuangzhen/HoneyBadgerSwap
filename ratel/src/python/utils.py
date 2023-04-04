import ast
import asyncio
import glob
import json
import shutil
from enum import IntEnum

import leveldb
import os
import time

from gmpy import binary, mpz
from gmpy2 import mpz_from_old_binary
from zkrp_pyo3 import pedersen_aggregate, pedersen_commit, zkrp_verify, zkrp_prove, zkrp_prove_mul, zkrp_verify_mul, \
    other_base_commit, other_base_commit_origin_H, product_com, gen_random_value, get_challenge


def parse_contract(name):
    contract = json.load(open(f'ratel/genfiles/build/contracts/{name}.json'))
    return contract['abi'], contract['bytecode']


def sign_and_send(tx, web3, account):
    signedTx = web3.eth.account.sign_transaction(tx, private_key=account.privateKey)
    tx_hash = web3.eth.send_raw_transaction(signedTx.rawTransaction)
    return web3.eth.wait_for_transaction_receipt(tx_hash)


def getAccount(web3, keystoreDir):
    for filename in os.listdir(keystoreDir):
        with open(keystoreDir + filename) as keyfile:
            encryptedKey = keyfile.read()
            privateKey = web3.eth.account.decrypt(encryptedKey, '')
            return web3.eth.account.privateKeyToAccount(privateKey)


class MultiAcquire(asyncio.Task):
    _check_lock = asyncio.Lock()  # to suspend for creating task that acquires objects
    _release_event = asyncio.Event()  # to suspend for any object was released

    def __init__(self, locks):
        super().__init__(self._task_coro())
        self._locks = locks
        # Here we use decorator to subscribe all release() calls,
        # _release_event would be set in this case:
        for l in self._locks:
            l.release = self._notify(l.release)

    async def _task_coro(self):
        while True:
            # Create task to acquire all locks and break on success:
            async with type(self)._check_lock:
                if not any(l.locked() for l in self._locks):  # task would be created only if all objects can be acquired
                    task = asyncio.gather(*[l.acquire() for l in self._locks])  # create task to acquire all objects
                    await asyncio.sleep(0)  # start task without waiting for it
                    break
            # Wait for any release() to try again:
            await type(self)._release_event.wait()
        # Wait for task:
        return await task

    def _notify(self, func):
        def wrapper(*args, **kwargs):
            type(self)._release_event.set()
            type(self)._release_event.clear()
            return func(*args, **kwargs)

        return wrapper


def mpcPort(seq, concurrency):
    if seq > 0:
        return mpc_port + seq % concurrency * 100
    else:
        return mpc_port + seq * 100


def key_preprocessed_element_data(element_type, idx):
    return f'data_{element_type}_{idx}'.encode()


def key_preprocessed_element_version(element_type, idx):
    return f'version_{element_type}_{idx}'.encode()


def key_zkrp_blinding_index(idx, num=1):
    return f'zkrp_blinding_index_{idx}_{num}'.encode()


def key_zkrp_blinding_commitment_index(idx):
    return f'zkrp_blinding_commitment_index_{idx}'.encode()


def key_zkrp_agg_commitment_index(idx):
    return f'zkrp_agg_commitment_index_{idx}'.encode()


def encode_key(key):
    key = key.lower()
    return f'{key}'.encode()


def key_state_mask(server_addr, idx):
    return f'state_mask_{server_addr}_{idx}'.encode()


def location_sharefile(server_id, base_port):
    return f'Persistence/Transactions-P{server_id}-{base_port}.data'


def location_db(server_id):
    db_path = os.getenv('DB_PATH', '/opt/hbswap/db')
    return f'{db_path}/server-{server_id}'


def location_prep_file(element_type, server_id, players):
    filepath = f'{prep_dir(element_type)}/{players}*/*P{server_id}'
    for file in glob.glob(filepath):
        return file


def prep_dir(element_type):
    return f'./preprocessing/{str(element_type)}'


def openDB(location):
    return leveldb.LevelDB(location)


def hex_to_int(x):
    x = mpz_from_old_binary(x)
    return int((x * inverse_R) % prime)


def int_to_hex(x):
    x = mpz(x)
    x = (x * R) % prime
    x = binary(int(x))
    x += b'\x00' * (32 - len(x))
    return x


def get_inverse(a):
    ret = 1
    b = prime - 2
    while b:
        if b % 2 == 1:
            ret = (ret * a) % prime
        b //= 2
        a = (a * a) % prime
    return ret


def recover_input(db, masked_value, idx):  # return: int
    try:
        input_mask_share = db.Get(key_preprocessed_element_data(PreprocessedElement.INT, idx))
    except KeyError:
        input_mask_share = bytes(0)
    input_mask_share = int.from_bytes(input_mask_share, 'big')
    return (masked_value - input_mask_share) % prime


def players(contract):
    players = contract.functions.N().call()
    return players


def threshold(contract):
    threshold = contract.functions.T().call()
    return threshold


def list_to_str(list):
    st = ''
    for v in list:
        st += f"{',' if len(st) > 0 else ''}{v}"
    return st


async def execute_cmd(cmd, info=''):
    retry = mpc_failed_retry
    while True:
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()

        print(f'[{cmd!r} exited with {proc.returncode}]')
        if info:
            print(f'[info]\n{info}')
        if stdout:
            print(f'[stdout]\n{stdout.decode()}')

        returncode = proc.returncode
        if returncode != 0:
            print('ERROR!')
            # print(f'[stderr]\n{stderr.decode()}')

        retry -= 1

        if retry <= 0 or returncode == 0:
            if returncode != 0:
                print('**** ERROR')

            return returncode


def mark_finish(server, seq):
    port = mpcPort(seq, server.concurrency)
    server.portLock[port].release()

    key = 'execHistory'
    exec_history = read_db(server, key)
    exec_history = bytes_to_dict(exec_history)

    exec_history[seq] = True

    exec_history = dict_to_bytes(exec_history)
    write_db(server, key, exec_history)


def read_db(server, key, finalize_on_chain=False):
    key = key.lower()
    try:
        value = server.db.Get(key.encode())
    except KeyError:
        value = bytes(0)

    if key in server.dbLock.keys():
        server.dbLockCnt[key] -= 1
        if server.dbLockCnt[key] == 0:
            if not finalize_on_chain:
                server.dbLock[key].release()

    return value


def write_db(server, key, value, finalize_on_chain=False):
    key = key.lower()
    server.db.Put(key.encode(), value)

    if key in server.dbLock.keys():
        server.dbLockCnt[key] -= 1
        if server.dbLockCnt[key] == 0:
            if not finalize_on_chain:
                server.dbLock[key].release()


def bytes_to_int(value):
    return int.from_bytes(value, 'big')


def bytes_to_list(value):
    try:
        value = value.decode(encoding='utf-8')
        value = list(ast.literal_eval(value))
    except:
        value = []
    return value


def bytes_to_dict(value):
    try:
        value = value.decode(encoding='utf-8')
        value = dict(ast.literal_eval(value))
    except:
        value = {}
    return value


def int_to_bytes(value):
    return value.to_bytes((value.bit_length() + 7) // 8, 'big')


def list_to_bytes(value):
    return bytes(str(value), encoding='utf-8')


def dict_to_bytes(value):
    return bytes(str(value), encoding='utf-8')


async def verify_proof(server, pflist):
    # print('verifying proof')
    blinding_idx_request = ""

    # times = []
    # times.append(time.perf_counter())

    for pfexp in pflist:
        [x, zkpstmt, type_Mul, y, r] = pfexp

        if type_Mul == 0:
            [idxValueBlinding, maskedValueBlinding, proof, commitment] = zkpstmt

            if proof is None or commitment is None or not zkrp_verify(proof, commitment):
                print("[Error]: Committed secret value does not pass range proof verification!")
                return False

            blinding = recover_input(server.db, maskedValueBlinding, idxValueBlinding)
            x, y, r = int(x), int(y), int(r)

            ###################################################

            pfval = x % prime
            if pfval < 0:
                pfval = (pfval % prime + prime) % prime

            value1_bytes = list(pfval.to_bytes(32, byteorder='little'))
            blinding_bytes = list(blinding.to_bytes(32, byteorder='little'))

            share_commitment = pedersen_commit(value1_bytes, blinding_bytes)

            server.zkrpShares[f'{idxValueBlinding}'] = share_commitment

            if len(blinding_idx_request):
                blinding_idx_request += ","
            blinding_idx_request += f"{idxValueBlinding}"

        else:  ### x * y >= r
            [idx_rx, masked_rx, idx_ry, masked_ry, prf, Cz] = zkpstmt
            rx = recover_input(server.db, masked_rx, idx_rx)
            ry = recover_input(server.db, masked_ry, idx_ry)

            if type_Mul >= 3:
                x = -x
                x = (x % prime + prime) % prime
            ############# (1) compute g^[x]h^[rx] #############
            x_bytes = list(x.to_bytes(32, byteorder='little'))
            rx_bytes = list(rx.to_bytes(32, byteorder='little'))
            g_x_share = pedersen_commit(x_bytes, rx_bytes)
            server.zkrpShares[f'{idx_rx}_{0}'] = g_x_share
            if len(blinding_idx_request):
                blinding_idx_request += ","
            blinding_idx_request += f"{idx_rx}_{0}"

            ############# (2) compute g^[y] #############
            y_bytes = list(y.to_bytes(32, byteorder='little'))
            ry_bytes = list(ry.to_bytes(32, byteorder='little'))
            g_y_share = pedersen_commit(y_bytes, ry_bytes)
            server.zkrpShares[f'{idx_ry}_{0}'] = g_y_share
            if len(blinding_idx_request):
                blinding_idx_request += ","
            blinding_idx_request += f"{idx_ry}_{0}"

    # times.append(time.perf_counter())
    results_list = await server.get_zkrp_shares(players(server.contract), blinding_idx_request)
    # times.append(time.perf_counter())

    blindingy_idx_request = ""
    cnt_res = 0
    for i in range(len(pflist)):
        results, pfexp = results_list[cnt_res], pflist[i]

        [x, zkpstmt, type_Mul, y, r] = pfexp

        if type_Mul == 0:
            agg_commitment = pedersen_aggregate(results, [x + 1 for x in list(range(server.players))])
            [idxValueBlinding, maskedValueBlinding, proof, commitment] = zkpstmt

            if agg_commitment != commitment:
                print('error:',i)
                print('agg_com:',agg_commitment)
                print('comm:',commitment)
                return False

        else:  ### x * y >= r
            # [idxValueBlinding, maskedValueBlinding, _proof, commitment] = zkpstmt
            # blinding = recover_input(server.db, maskedValueBlinding, idxValueBlinding)
            # x, y, r = int(x), int(y), int(r)

            [idx_rx, masked_rx, idx_ry, masked_ry, prf, Cz] = zkpstmt
            [Kx,Ky,Kz,sx,sy,sx_prime,sy_prime,sz_prime,c] = prf

            rx = recover_input(server.db, masked_rx, idx_rx)
            ry = recover_input(server.db, masked_ry, idx_ry)

            results_Cx = results
            Cx_bytes = pedersen_aggregate(results_Cx, [x + 1 for x in list(range(server.players))])
            cnt_res = cnt_res + 1

            results_Cy = results_list[cnt_res]
            Cy_bytes = pedersen_aggregate(results_Cy, [x + 1 for x in list(range(server.players))])
            
            # ############# (2) compute (g^x)^[y] * h^[rz] #############
            # rz_bytes = list(blinding.to_bytes(32, byteorder='little'))
            # y_bytes = list(y.to_bytes(32, byteorder='little'))
            # g_xy_h_rz_bytes = other_base_commit(g_x_bytes, y_bytes, rz_bytes)
            # server.zkrpShares[f'{idxValueBlinding}_{1}'] = g_xy_h_rz_bytes

            # if len(blindingy_idx_request):
            #     blindingy_idx_request += ","
            # blindingy_idx_request += f"{idxValueBlinding}_{1}"

            ############# (2) compute (g^sx) * h^sx_prime =?= Cx^c * Kx #############
            sx_bytes = list(sx.to_bytes(32, byteorder='little'))
            sx_prime_bytes = list(sx_prime.to_bytes(32, byteorder='little'))
            Csx = pedersen_commit(sx_bytes,sx_prime_bytes)

            c_bytes = list(c.to_bytes(32, byteorder='little'))
            Cx_c = other_base_commit_origin_H(Cx_bytes,c_bytes,zer_bytes)
            Csx_rhs = product_com(Cx_c,Kx,one_bytes)

            if Csx != Csx_rhs:
                print('Csx:',Csx)
                print('Csx_rhs:',Csx_rhs)
                return False
            
            ############# (3) compute (g^sy) * h^sy_prime =?= Cy^c * Ky #############
            sy_bytes = list(sy.to_bytes(32, byteorder='little'))
            sy_prime_bytes = list(sy_prime.to_bytes(32, byteorder='little'))
            Csy = pedersen_commit(sy_bytes,sy_prime_bytes)

            Cy_c = other_base_commit_origin_H(Cy_bytes,c_bytes,zer_bytes)
            Csy_rhs = product_com(Cy_c,Ky,one_bytes)

            if Csy != Csy_rhs:
                print('Csy:',Csy)
                print('Csy_rhs:',Csy_rhs)
                return False
        
            ############# (4) compute (Cx^sy) * h^sz_prime =?= Cz^c * Kz #############
            sz_prime_bytes = list(sz_prime.to_bytes(32, byteorder='little'))
            Cz_lhs = other_base_commit_origin_H(Cx_bytes, sy_bytes, sz_prime_bytes)

            Cz_c = other_base_commit_origin_H(Cz,c_bytes,zer_bytes)
            Cz_rhs = product_com(Cz_c,Kz,one_bytes)

            if Cz_lhs != Cz_rhs:
                print('Cz_lhs:',Cz_lhs)
                print('Cz_rhs:',Cz_rhs)
                return False

        cnt_res = cnt_res + 1

    # times.append(time.perf_counter())

    # if len(blindingy_idx_request):
    #     resultsy_list = await server.get_zkrp_shares(players(server.contract), blindingy_idx_request)
    #     # times.append(time.perf_counter())

    #     idx_y = 0
    #     for i in range(len(pflist)):
    #         pfexp = pflist[i]

    #         [x, zkpstmt, type_Mul, y, r] = pfexp
    #         [idxValueBlinding, maskedValueBlinding, proof, commitment] = zkpstmt

    #         if type_Mul != 0:
    #             r = -r
    #             r = (r % prime + prime) % prime

    #             results_g_xy_h_rz = resultsy_list[idx_y]
    #             agg_gxyhrz_commitment = pedersen_aggregate(results_g_xy_h_rz,
    #                                                        [x + 1 for x in list(range(server.players))])

    #             r_bytes = list(r.to_bytes(32, byteorder='little'))
    #             g_r = pedersen_commit(r_bytes, zer_bytes)

    #             agg_commitment = product_com(g_r, agg_gxyhrz_commitment)
    #             if agg_commitment != commitment:
    #                 return False

    #             idx_y = idx_y + 1

    # times.append(time.perf_counter())
    # with open(f'ratel/benchmark/data/latency_zkrp_verify_{server.serverID}.csv', 'a') as f:
    #     for op, t in enumerate(times):
    #         f.write(f'trade\t'
    #                 f'op\t{op + 1}\t'
    #                 f'cur_time\t{t}\n')

    return True


def get_zkrp(secret_value, exp_str, r, isSfix=False):
    print(f'get_zkrp {secret_value} {exp_str} {r}')

    value = secret_value

    if isSfix:
        value = int(value * fp)
        r = int(r * fp)

    if exp_str == '>=':
        value = value - r
    elif exp_str == '>':  # secret_value > r <==> secret_value - r -1 >= 0
        value = value - r - 1
    elif exp_str == '<=':  # secret_value <= r <==> r - secret_value >= 0
        value = r - value
    elif exp_str == '<':  # secret_value < r <==> r - secret_value - 1 >= 0
        value = r - value - 1

    value = (value % prime + prime) % prime

    # To prove value >= 0
    bits = 32
    proof, commitment, blinding_bytes = zkrp_prove(value, bits)
    blinding = int.from_bytes(blinding_bytes, byteorder='little')
    return proof, commitment, blinding

def generate_zkrp_mul(x, y, exp_str, r):
    rv_list_bytes = gen_random_value(8)
    rv_list = []
    for i in range(len(rv_list_bytes)):
        rv_list.append(int.from_bytes(rv_list_bytes[i], byteorder='little'))
    rx, ry, rz, kx, ky, kx_prime, ky_prime, kz_prime = rv_list[0], rv_list[1], rv_list[2], rv_list[3], rv_list[4], rv_list[5], rv_list[6], rv_list[7]

    if exp_str == '>=':
        z = x*y - r
    elif exp_str == '>':  # secret_value > r <==> secret_value - r -1 >= 0
        z = x*y - r - 1
    elif exp_str == '<=':  # secret_value <= r <==> r - secret_value >= 0
        z = r - x*y
        x = (prime-x)%prime
    elif exp_str == '<':  # secret_value < r <==> r - secret_value - 1 >= 0
        z = r - x*y - 1
        x = (prime-x)%prime

    z = (x*y+prime) % prime
    x = (x%prime + prime) % prime
    y = (y%prime + prime) % prime

    x_bytes, y_bytes, z_bytes = x.to_bytes(32, byteorder='little'), y.to_bytes(32, byteorder='little'), z.to_bytes(32, byteorder='little')
    blinding_z = (rx * y + rz) % prime
    rx_bytes, ry_bytes, blinding_z_bytes = rx.to_bytes(32, byteorder='little'), ry.to_bytes(32, byteorder='little'), blinding_z.to_bytes(32, byteorder='little')
    Cx, Cy, Cz = pedersen_commit(x_bytes,rx_bytes), pedersen_commit(y_bytes,ry_bytes), pedersen_commit(z_bytes, blinding_z_bytes)

    # print('Cx:',Cx)
    # print('Cy:',Cy)

    z_v, blinding_kz = (x*ky) % prime, (rx * ky % prime + kz_prime) % prime
    kx_bytes, ky_bytes, z_v_bytes = kx.to_bytes(32, byteorder='little'), ky.to_bytes(32, byteorder='little'), z_v.to_bytes(32, byteorder='little')
    kx_prime_bytes, ky_prime_bytes, blinding_kz_bytes = kx_prime.to_bytes(32, byteorder='little'), ky_prime.to_bytes(32, byteorder='little'), blinding_kz.to_bytes(32, byteorder='little')
    Kx, Ky, Kz = pedersen_commit(kx_bytes, kx_prime_bytes), pedersen_commit(ky_bytes, ky_prime_bytes), pedersen_commit(z_v_bytes, blinding_kz_bytes)

    c_bytes = get_challenge(Kx, Ky, Kz)
    c = int.from_bytes(c_bytes, byteorder='little')

    sx, sy, sx_prime, sy_prime, sz_prime = (c*x + kx) % prime, (c*y + ky) % prime, (c*rx + kx_prime) % prime, (c*ry + ky_prime) % prime, (c*rz + kz_prime) % prime
    # print(sx,sy,sx_prime,sy_prime)

    prf = (Kx,Ky,Kz,sx,sy,sx_prime,sy_prime,sz_prime,c)

    # print('sx:',sx)
    # print('test:',pedersen_commit(zer_bytes,zer_bytes))
    # sx_bytes = list(sx.to_bytes(32, byteorder='little'))
    # sx_prime_bytes = list(sx_prime.to_bytes(32, byteorder='little'))
    # C_sx = pedersen_commit(sx_bytes, sx_prime_bytes)
    # # print("C_sx:",C_sx)
    # c_bytes1 = list(c.to_bytes(32, byteorder='little'))
    # Cx_c = other_base_commit_origin_H(Cx,c_bytes1,zer_bytes)
    # # print('Cx_c',Cx_c)
    # Csx_rhs1 = product_com(Cx_c,Kx,one_bytes)
    # # print('Csx_rhs1:',Csx_rhs1)
    # # print('Kx',Kx)
    
    # # print('sy:',sy)
    # sy_bytes = list(sy.to_bytes(32, byteorder='little'))
    # sy_prime_bytes = list(sy_prime.to_bytes(32, byteorder='little'))
    # C_sy = pedersen_commit(sy_bytes, sy_prime_bytes)
    # # print("C_sy:",C_sy)
    # Cy_c = other_base_commit_origin_H(Cy,c_bytes1,zer_bytes)
    # Csy_rhs1 = product_com(Cy_c,Ky,one_bytes)
    # print('Csy_rhs1:',Csy_rhs1)
    # sz_prime_bytes = list(sz_prime.to_bytes(32, byteorder='little'))
    # Cz_lhs = other_base_commit_origin_H(Cx, sy_bytes, sz_prime_bytes)

    # Cz_c = other_base_commit_origin_H(Cz,c_bytes1,zer_bytes)
    # Cz_rhs = product_com(Cz_c,Kz,one_bytes)

    # print('Cz_lhs:',Cz_lhs)
    # print('Cz_rhs:',Cz_rhs)

    # time.sleep(50000)

    return Cz,prf,rx,ry



class PreprocessedElement(IntEnum):
    INT = 0
    BIT = 1
    TRIPLE = 2


def touch_dir(path):
    is_exist = os.path.exists(path)
    if not is_exist:
        os.makedirs(path)


async def run_online(server_id, port, players, threshold, mpcProg, server, seq=0):
    data_dir = f'offline_data/s{server_id}/{mpcProg}_port_{port}'
    touch_dir(data_dir)
    shutil.rmtree(data_dir)
    touch_dir(f'{data_dir}/{players}-MSp-{prime_bit_length}')

    with open(f'{data_dir}/{players}-MSp-{prime_bit_length}/Params-Data', 'w') as f:
        f.write(str(prime))

    preprocessing_req_file = f'/usr/src/hbswap/ratel/mpc_out/{mpcProg}.txt'
    with open(preprocessing_req_file, 'r') as f:
        for line in f.readlines():
            element = line.split()
            if element[1] == 'integer':
                num = ((int(element[0]) - 1) // BUFFER_SIZE + 1) * BUFFER_SIZE
                element_type = element[2][:-1].upper()

                init_index = eval(f'server.contract.functions.initIndex{element_type}')(seq, mpcProg).call()
                print('init_index', init_index)

                data = b''
                for index in range(init_index, init_index + num, BUFFER_SIZE):
                    chunk = server.db.Get(key_preprocessed_element_data(PreprocessedElement[element_type], index))
                    data += chunk

                file = f'{data_dir}/{players}-MSp-{prime_bit_length}/{element[2].capitalize()}-MSp-P{server_id}'
                print(f'write to {file}')
                with open(file, "wb") as out_f:
                    out_f.write(mal_shamir_sig + data)

    cmd = f'{prog} -N {players} -T {threshold} -p {server_id} -pn {port} -P {prime} -ip HOSTS.txt -F --prep-dir {data_dir} -npfs {mpcProg}'
    await execute_cmd(cmd, f'**** task seq {seq}')


async def run_offline(server_id, port, players, threshold, mpcProg):
    dir = f'offline_data/s{server_id}/{mpcProg}_port_{port}'
    cmd = f'{offline_prog} -N {players} -T {threshold} -p {server_id} -pn {port} -P {prime} -ip HOSTS.txt --prep-dir {dir} -npfs {mpcProg}'
    await execute_cmd(cmd)


async def run_online_ONLY(server_id, port, players, threshold, mpcProg):
    cmd = f'{prog} -N {players} -T {threshold} -p {server_id} -pn {port} -P {prime} -ip HOSTS.txt -npfs {mpcProg}'
    await execute_cmd(cmd)



prog = './malicious-shamir-party.x'
offline_prog = './mal-shamir-offline.x'
random_int_prog = './random-shamir.x'
random_bit_prog = './random-bits.x'
random_triple_prog = './random-triples.x'

mal_shamir_sig = b'/\x00\x00\x00\x00\x00\x00\x00Shamir gfp\x00 \x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14\xde\xf9\xde\xa2\xf7\x9c\xd6X\x12c\x1a\\\xf5\xd3\xed'

### blsPrime
# prime = 52435875175126190479447740508185965837690552500527637822603658699938581184513
# R = 10920338887063814464675503992315976177888879664585288394250266608035967270910
# prime_bit_length = 255

### Ristretto group order
prime = 7237005577332262213973186563042994240857116359379907606001950938285454250989
R = 7237005577332262213973186563042994240413239274941949949428319933631315875101
prime_bit_length = 253
inverse_R = get_inverse(R)

inv_10 = 723700557733226221397318656304299424085711635937990760600195093828545425099
zer = 0
zer_bytes = list(zer.to_bytes(32, byteorder='little'))
one_number = 1
one_bytes = list(one_number.to_bytes(32, byteorder='little'))

fp = 2 ** 16
decimal = 10 ** 15
sz = 32

http_host = "0.0.0.0"
http_port = 4000

mpc_port = 5000

threshold_available_preprocessed_elements = 1000
preprocessed_element_gen_batch_size = 10000

BUFFER_SIZE = 100
bit_size = 32
chunk_size = {
    PreprocessedElement.INT: 1,
    PreprocessedElement.BIT: BUFFER_SIZE,
    PreprocessedElement.TRIPLE: BUFFER_SIZE,
}

confirmation = 2

trade_key_num = 7

repeat_experiment = 1

mpc_failed_retry = 3

sleep_time = 0.01
