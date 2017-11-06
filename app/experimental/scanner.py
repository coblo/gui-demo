#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Scan network for Running Nodes"""
import asyncio
import time

now = time.time()


async def check_port(ip, port, loop):
    try:
        reader, writer = await asyncio.open_connection(ip, port, loop=loop)
        print(ip, port, 'ok')
        writer.close()
        return (ip, port, True)
    except:
        return (ip, port, False)


async def check_port_sem(sem, ip, port, loop):
    async with sem:
        return await check_port(ip, port, loop)


async def run(dests, ports, loop):
    sem = asyncio.Semaphore(400)
    tasks = [asyncio.ensure_future(check_port_sem(sem, d, p, loop)) for d in dests for p in ports]
    responses = await asyncio.gather(*tasks)
    return responses

dests = ['192.168.2.{}'.format(x) for x in range(256)]
ports = [8374, 8375]

loop = asyncio.get_event_loop()
future = asyncio.ensure_future(run(dests, ports, loop))
loop.run_until_complete(future)
print('#'*50)
print('Results: ', future.result())
print('#'*50)
print('Total time: ', time.time() - now)