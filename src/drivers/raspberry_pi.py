import logging
import math

import cv2
from drivers import ArmDriver, ChassisDriver
from PIL import Image

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
def make_serial(c) -> serial.Serial:
    if c in ser:
        return ser[c]
    ser[c] = serial.Serial(c, 9600, timeout=1)
    return ser[c]

class RaspberryPiChassisDriver(ChassisDriver):
    def __init__(self):
        self.logger = logging.getLogger(f"RaspberryPiChassisDriver")
        self.serial = make_serial('/dev/ttyACM0')

    async def move(self, direction: float, speed: float, distance: float = -1.0):
        self.logger.debug('move %s %s %s', direction, speed, distance)
        if speed == 0:
            self.serial.write('s')
        elif -math.pi / 4 < direction < math.pi / 4:
            self.serial.write('f')
        elif math.pi / 4 < direction < math.pi * 3 / 4:
            self.serial.write('l')
        elif - math.pi * 3 / 4 < direction < - math.pi / 4:
            self.serial.write('r')
        else:
            self.serial.write('b')


    async def rotate(self, speed: float):
        self.logger.debug('rotate %s', speed)
        if speed > 0:
            self.serial.write('L')
        else:
            self.serial.write('R')


class RaspberryPiArmDriver(ArmDriver):
    def __init__(self, camera_id):
        self.logger = logging.getLogger(f"RaspberryPiArmDriver({camera_id})")
        self.camera = cv2.VideoCapture(camera_id)
        self.serial = make_serial('/dev/ttyACM0')
    async def arm_up(self, speed):
        self.logger.debug('arm up %s', speed)
        pass

    async def arm_spray(self, time):
        self.logger.debug('arm spray %s', time)
        pass

    def capture_image_raw(self):
        self.logger.debug('capture image raw')
        return_value, image = self.camera.read()
        return image
