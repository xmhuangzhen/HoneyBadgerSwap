import asyncio
import re

from aiohttp import ClientSession
from ratel.src.python.utils import http_port, http_host, get_inverse, prime, sign_and_send


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


def interpolate(x, points, t):
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
    res = []
    batch_size = len(batch_points[0][1])
    players = len(batch_points)
    for i in range(batch_size):
        points = []
        for j in range(players):
            result = int(batch_points[j][1][i])
            if result != 0:
                points.append((batch_points[j][0], result))
        res.append(interpolate(x, points, threshold))
    return res


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
        task = send_request(f"http://{http_host}:{http_port + server_id}/{request}")
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results


async def get_inputmasks(players, inputmask_idxes, threshold):
    request = f"inputmasks/{inputmask_idxes}"
    results = await send_requests(players, request)
    batch_points = []
    for i in range(len(results)):
        if len(results[i]):
            batch_points.append((i + 1, re.split(",", results[i]["inputmask_shares"])))

    inputmasks = batch_interpolate(0, batch_points, threshold)

    return inputmasks
