#!/usr/bin/env python3
import asyncio
import logging

from drivers.raspberry_pi import RaspberryPiChassisDriver

async def process(chassis: RaspberryPiChassisDriver, cmd: str):
    spt = cmd.split()
    cmd = spt[0]
    if cmd == 'move':
        await chassis.move(float(spt[1]), float(spt[2]))
    elif cmd == 'rotate':
        await chassis.rotate(float(spt[1]))


async def main():
    chassis = RaspberryPiChassisDriver()
    cmd = ''
    while cmd != 'exit':
        cmd = input('> ')
        try:
            await process(chassis, cmd)
        except Exception as e:
            logging.error("failed to run command: " + cmd ,exc_info=e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
