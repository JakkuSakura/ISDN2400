import asyncio
import logging
import math

import cv2
import numpy as np

from drivers import ArmDriver, ChassisDriver

import serial
import time

"""
['f',#forward
'b',#backward
'l',#leftward
'r',#rightward
'L',#turnleft
'R',#turnright
'S']:#stop
"""
ser = {}

SERIAL_PORT = '/dev/ttyUSB0'


def make_serial(c) -> serial.Serial:
    if c in ser:
        return ser[c]
    ser[c] = serial.Serial(c, 9600, timeout=1)
    return ser[c]


def write_command(s: serial.Serial, c, timeout=1):
    logging.debug("Writing command: %s", c)
    try:
        for i in range(3):
            s.write((c + '\n').encode('utf-8'))
        s.flush()
        time.sleep(0.05)
        while True:
            r = s.readline()
            if not r:
                break
            logging.debug("Read echo: %s", str(r))
    # TODO: timeout
    except serial.serialutil.SerialException as e:
        logging.error("Error writing to serial port", exc_info=e)
        return False


class RaspberryPiChassisDriver(ChassisDriver):
    def __init__(self):
        self.logger = logging.getLogger(f"RaspberryPiChassisDriver")
        self.serial = make_serial(SERIAL_PORT)

    async def move(self, direction: float, speed: float, distance: float = -1.0):
        self.logger.debug('move %s %s %s', direction, speed, distance)
        if abs(speed) < 0.5:
            write_command(self.serial, 'S')
        elif -math.pi / 4 < direction < math.pi / 4:
            write_command(self.serial, 'f')
        elif math.pi / 4 < direction < math.pi * 3 / 4:
            write_command(self.serial, 'l')
        elif - math.pi * 3 / 4 < direction < - math.pi / 4:
            write_command(self.serial, 'r')
        else:
            write_command(self.serial, 'b')

    async def rotate(self, speed: float):
        self.logger.debug('rotate %s', speed)
        if abs(speed) < 0.5:
            write_command(self.serial, 'S')
        elif speed > 0:
            write_command(self.serial, 'R')
        else:
            write_command(self.serial, 'L')


class RaspberryPiArmDriver(ArmDriver):
    def __init__(self, camera_id):
        self.logger = logging.getLogger(f"RaspberryPiArmDriver({camera_id})")
        self.camera = cv2.VideoCapture(camera_id)
        self.serial = make_serial(SERIAL_PORT)

    def servo_command(self, servo: int, speed: float):
        # speed_min = 0
        # speed_max = 3000
        speed_mid, speed_spread = {
            1: (1500, -200)

        }[servo]

        return str(servo) + '-' + str(int(speed_mid + speed * speed_spread))

    async def arm_up(self, speed):
        self.logger.debug('arm up %s', speed)
        if abs(speed) > 0.5:
            write_command(self.serial, self.servo_command(1, speed))
            await asyncio.sleep(0.5)
            write_command(self.serial, self.servo_command(1, 0))
        else:
            write_command(self.serial, self.servo_command(1, 0))

    async def arm_spray(self, time):
        self.logger.debug('arm spray %s', time)
        write_command(self.serial, 'on')
        await asyncio.sleep(time)
        write_command(self.serial, 'off')

    def capture_image_raw(self):
        self.logger.debug('capture image raw')
        return_value, image = self.camera.read()
        self.logger.debug('capture image raw: %s', return_value)
        if return_value:
            return image
        else:
            return np.zeros((600, 800, 3), np.uint8)
