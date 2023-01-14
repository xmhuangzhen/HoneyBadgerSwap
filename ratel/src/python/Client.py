import asyncio
import re

from aiohttp import ClientSession
from ratel.src.python.utils import http_port, http_host, get_inverse, prime, sign_and_send
from zkrp_pyo3 import zkrp_prove_mul, zkrp_verify_mul


def reserveInput(web3, appContract, num, account):
    tx = appContract.functions.reserveInput(num).buildTransaction({'from': account.address, 'gas': 1000000, 'nonce': web3.eth.get_transaction_count(account.address)})
    receipt = sign_and_send(tx, web3, account)
    log = appContract.events.ReserveInputMask().processReceipt(receipt)
    return log[0]['args']['inputMaskIndexes']


def evaluate(x, points):
    value = 0
    n = len(points)
    for i in range(n):
        tot = 1
        for j in range(n):
            if i == j:
                continue
            tot = tot * (x - points[j][0]) * get_inverse(points[i][0] - points[j][0]) % prime
        value = (value + points[i][1] * tot) % prime
    return value


def interpolate(points, x, t):
    assert len(points) > t
    value = evaluate(x, points[:t + 1])
    n = len(points)
    for i in range(t + 2, n + 1):
        check = evaluate(x, points[:i])
        if check != value:
            print('mac_fail')
            return 0
    return value % prime


def batch_interpolate(x, batch_points, threshold):
    batch_size = len(batch_points[0][1])
    players = len(batch_points)

    list_points = []
    for i in range(batch_size):
        points = []
        for j in range(players):
            result = int(batch_points[j][1][i])
            if result != 0:
                points.append((batch_points[j][0], result))
        list_points.append(points)

    import multiprocessing
    from functools import partial

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        return pool.map(partial(interpolate, x=x, t=threshold), list_points)


async def send_request(url):
    async with ClientSession() as session:
        try:
            async with session.get(url) as resp:
                json_response = await resp.json()
                return json_response
        except:
            return ''


async def send_requests(players, request, self_id = -1):
    tasks = []
    for server_id in range(players):
        if server_id == self_id:
            continue
        task = send_request(f'http://{http_host}:{http_port + server_id}/{request}')
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results


def reconstruct_values(results, key, threshold):
    batch_points = []
    for i in range(len(results)):
        if len(results[i]):
            batch_points.append((i + 1, re.split(',', results[i][key])))

    values = batch_interpolate(0, batch_points, threshold)

    return values



async def get_inputmasks(players, inputmask_idxes, threshold):
    request = f'inputmasks/{inputmask_idxes}'
    results = await send_requests(players, request)
    return reconstruct_values(results, 'inputmask_shares', threshold)


async def get_secret_values(players, keys, threshold):
    request = f'query_secret_values/{keys}'
    results = await send_requests(players, request)
    return reconstruct_values(results, 'secret_shares', threshold)


async def get_zkrp_blinding_info(players, num, threshold):
    request_blinding = f'zkrp_blinding_shares/{num}'
    blinding_res = await send_requests(players, request_blinding)
    
    for i in range(len(blinding_res)):
        blinding_res[i] = re.split(',',blinding_res[i]['zkrp_blinding_shares'])
    blinding_prime = batch_interpolate(blinding_res, threshold)

    request_agg = f'zkrp_new_agg_com/{num}'
    comm_res = await send_requests(players, request_agg)
    comm_res = comm_res[0]['zkrp_blinding_info_2']
    comm_res = re.split(';', comm_res)
    for i in range(len(comm_res)):
        comm_res[i] = re.split(',', comm_res[i][1:-1])
        for j in range(len(comm_res[i])):
            comm_res[i][j] = int(comm_res[i][j])

    return blinding_prime, comm_res

async def generate_zkrp_mul(players, x, y, threshold):
    blinding_prime_list, blinding_comm_list = await get_zkrp_blinding_info(players, 2, threshold)

    print('blinding prime list:', blinding_prime_list)
    print('blinding com list:', blinding_comm_list)

    rx_prime, ry_prime = blinding_prime_list[0], blinding_prime_list[1]
    cx_bytes, cy_bytes = blinding_comm_list[0], blinding_comm_list[1]

    rx_prime_bytes =  rx_prime.to_bytes((rx_prime.bit_length() + 7) // 8, 'little')
    ry_prime_bytes =  ry_prime.to_bytes((ry_prime.bit_length() + 7) // 8, 'little')

    mx_prime, my_prime, sx, sy_prime,  = zkrp_prove_mul(x, y, rx_prime_bytes,ry_prime_bytes)

