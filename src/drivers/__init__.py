import logging
import numpy as np

logger = logging.getLogger('drivers')


class ChassisDriver:
    async def move(self, direction: float, speed: float, distance: float = None):
        logger.debug('move %s %s %s', direction, speed, distance)
        pass

    async def rotate(self, speed: float):
        logger.debug('rotate %s', speed)
        pass


class ArmDriver:
    async def arm(self, speed):
        logger.debug('arm up %s', speed)
        pass

    async def servo(self, servo: int, speed: float):
        logger.debug('servo %s %s', servo, speed)
        pass

    async def spray(self, speed):
        logger.debug('arm spray %s', speed)
        pass

    def capture_image_raw(self):
        logger.debug('capture image')
        return np.zeros((600, 800, 3), np.uint8)
