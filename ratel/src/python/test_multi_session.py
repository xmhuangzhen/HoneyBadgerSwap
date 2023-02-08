import asyncio
import time

from aiohttp import web, ClientSession, TCPConnector

# async def multiple_sessions(app):
#    app[persistent_session_1] = session_1 = aiohttp.ClientSession()
#    app[persistent_session_2] = session_2 = aiohttp.ClientSession()
#    app[persistent_session_3] = session_3 = aiohttp.ClientSession()
#
#    yield
#
#    await asyncio.gather(
#        session_1.close(),
#        session_2.close(),
#        session_3.close(),
#    )

async def persistent_session(app):
    app['persistent_session'] = session = ClientSession()
    yield
    await session.close()
#
# async def my_request_handler(url):
#     session = app[persistent_session]
#     async with session.get(url) as resp:
#         print(resp.status)

async def main():
    times = []
    times.append(time.perf_counter())

    # app = web.Application()
    # app.cleanup_ctx.append(persistent_session)

    # session = request.app['PERSISTENT_SESSION']
    session = ClientSession()
    times.append(time.perf_counter())
    print('!', times[-1] - times[-2])

    url = 'http://0.0.0.0:4000/inputmasks/291,292,293,294,295'
    async with session.get(url) as resp:
        json_response = await resp.json()
        # print(json_response)
        times.append(time.perf_counter())
        print('!', times[-1] - times[-2])

    async with session.get(url) as resp:
        json_response = await resp.json()
        # print(json_response)
        times.append(time.perf_counter())
        print('!', times[-1] - times[-2])


    url = 'http://0.0.0.0:4001/inputmasks/291,292,293,294,295'
    async with session.get(url) as resp:
        json_response = await resp.json()
        # print(json_response)
        times.append(time.perf_counter())
        print('!!!', times[-1] - times[-2])

    url = 'http://0.0.0.0:4001/query_secret_values/balance_0x0000000000000000000000000000000000000000_0xc8206540e1553206597Fe74aE993e4f94Ac79B81,balance_0xea53C26EA09eDdbf07B71902d08507b2ebB7DB96_0xc8206540e1553206597Fe74aE993e4f94Ac79B81'
    async with session.get(url) as resp:
        json_response = await resp.json()
        print(json_response)
        times.append(time.perf_counter())
        print('!!!', times[-1] - times[-2])

    url = 'http://0.0.0.0:4001/inputmasks/291,292,293,294,295'
    async with session.get(url) as resp:
        json_response = await resp.json()
        # print(json_response)
        times.append(time.perf_counter())
        print('!!!', times[-1] - times[-2])


    await session.close()

if __name__=='__main__':
    # app = web.Application()
    # app.cleanup_ctx.append(persistent_session)
    # # persistent_session = web.AppKey("persistent_session", ClientSession)
    # url = 'http://0.0.0.0:4000/inputmasks/291,292,293,294,295'
    # asyncio.run(my_request_handler(url))
    asyncio.run(main())