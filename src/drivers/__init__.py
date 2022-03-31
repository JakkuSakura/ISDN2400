import logging

logger = logging.getLogger('drivers')
class ChassisDriver:
    async def move_front(self, distance, speed):
        logger.debug('move front %s %s', distance, speed)
        pass

    async def move_back(self, distance, speed):
        logger.debug('move back %s %s', distance, speed)
        pass

    async def move_left(self, distance, speed):
        logger.debug('move left %s %s', distance, speed)
        pass

    async def move_right(self, distance, speed):
        logger.debug('move right %s %s', distance, speed)
        pass

    async def rotate(self, angle, speed):
        logger.debug('rotate %s %s', angle, speed)
        pass


class ArmDriver:
    async def arm_up(self, distance):
        logger.debug('arm up %s', distance)
        pass

    async def arm_down(self, distance):
        logger.debug('arm down %s', distance)
        pass

    async def arm_spray(self, time):
        logger.debug('arm spray %s', time)
        pass

    def capture_image(self):
        logger.debug('capture image %s')
        pass
