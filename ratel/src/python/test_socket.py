import asyncio
import socket
import time

from ratel.src.python.utils import http_host, http_port, BUFLEN

async def send(reader, writer, req):
    req += '\n'
    print(f'Send: {req!r}')
    writer.write(req.encode())
    await writer.drain()

    data = await reader.readline()
    print(f'Received: {data.decode()!r}')

async def session():

    start_time = time.perf_counter()

    reader, writer = await asyncio.open_connection(http_host, http_port + 100)

    print(time.perf_counter() - start_time)

    await send(reader, writer, 'lala')

    print(time.perf_counter() - start_time)

    await send(reader, writer, 'asdf')

    print(time.perf_counter() - start_time)

    print('Close the connection')
    writer.close()

if __name__=='__main__':

    asyncio.run(session())

    # sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sk.connect((http_host, http_port + 100))
    #
    # print(time.perf_counter() - start_time)
    #
    # req = f'{239}'
    # sk.send(req.encode())
    # recv = sk.recv(BUFLEN).decode()
    # print(recv)
    #
    # print(time.perf_counter() - start_time)
    #
    # req = 'asdf'
    # sk.send(req.encode())
    # recv = sk.recv(BUFLEN).decode()
    # print(recv)
    #
    # print(time.perf_counter() - start_time)


