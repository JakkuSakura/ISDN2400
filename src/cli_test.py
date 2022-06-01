#!/usr/bin/env python3
import asyncio
import logging

from drivers.raspberry_pi import RaspberryPiChassisDriver, RaspberryPiArmDriver


async def process(chassis: RaspberryPiChassisDriver, arm: RaspberryPiArmDriver, cmd: str):
    spt = cmd.split()
    cmd = spt[0]
    if cmd == 'move':
        await chassis.move(float(spt[1]), float(spt[2]))
    elif cmd == 'rotate':
        await chassis.rotate(float(spt[1]))
    elif cmd == 'spray':
        await arm.spray(float(spt[1]))
    elif cmd == 'arm':
        await arm.arm(float(spt[1]))
    else:
        raise Exception("unknown command: " + cmd)

async def main():
    chassis = RaspberryPiChassisDriver()
    arm = RaspberryPiArmDriver(0)
    cmd = ''
    while cmd != 'exit':
        cmd = input('> ')
        try:
            await process(chassis, arm, cmd)
        except Exception as e:
            logging.error("failed to run command: " + cmd ,exc_info=e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
