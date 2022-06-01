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
    s = serial.Serial(c, 9600, timeout=1)

    ser[c] = s
    return s


def write_command(s: serial.Serial, c, timeout=1):
    logging.debug("Writing command: %s", c)
    try:
        for i in range(1):
            s.write((c + '\n').encode('utf-8'))
        s.flush()

        r = s.read_all()
        if r:
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
        begin = time.time()
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
        duration = time.time() - begin
        self.logger.debug('move %s %s %s time: %ss', direction, speed, distance, duration)


    async def rotate(self, speed: float):
        self.logger.debug('rotate %s', speed)
        if abs(speed) < 0.5:
            write_command(self.serial, 'S')
        elif speed > 0:
            write_command(self.serial, 'L')
        else:
            write_command(self.serial, 'R')


class RaspberryPiArmDriver(ArmDriver):
    def __init__(self, camera_id):
        self.logger = logging.getLogger(f"RaspberryPiArmDriver({camera_id})")
        self.camera = cv2.VideoCapture(camera_id)
        self.serial = make_serial(SERIAL_PORT)

    def servo_command(self, servo: int, speed: float):
        # speed_min = 0
        # speed_max = 3000
        # 1570
        speed_mid, speed_spread_down, speed_spread_up = {
            1: (1550, 150, 200),
            # 2: (1520, 500, 500),
            3: (1500, 100, 100),

        }[servo]

        if speed > 0:
            code = speed_mid + speed * speed_spread_up
        else:
            code = speed_mid + speed * speed_spread_down

        return str(servo) + '-' + str(int(code))

    async def servo(self, servo: int, speed: float):
        self.logger.debug('servo %s %s', servo, speed)
        if abs(speed) > 0.5:
            write_command(self.serial, self.servo_command(servo, speed))
        else:
            write_command(self.serial, self.servo_command(servo, 0))

    async def arm(self, speed):
        self.logger.debug('arm up %s', speed)
        servos = [1, 3]
        if abs(speed) > 0.5:
            for s in servos:
                write_command(self.serial, self.servo_command(s, speed))
        else:
            for s in servos:
                write_command(self.serial, self.servo_command(s, 0))

    async def spray(self, speed):
        self.logger.debug('arm spray %s', speed)
        if speed > 0:
            write_command(self.serial, 'on')
        else:
            write_command(self.serial, 'off')

    def capture_image_raw(self):
        self.logger.debug('capture image raw')
        return_value, image = self.camera.read()
        self.logger.debug('capture image raw: %s', return_value)
        if return_value:
            return image
        else:
            return np.zeros((600, 800, 3), np.uint8)
