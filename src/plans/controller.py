import logging

from drivers import ChassisDriver, ArmDriver


class Controller:
    def __init__(self, chassis_driver: ChassisDriver, arm_driver: ArmDriver):
        self.chassis_driver = chassis_driver
        self.arm_driver = arm_driver
        self.is_running = False
        self.route = []
        self.logger = logging.getLogger(type(self).__name__)
    
    async def drive(self):
        self.is_running = True
        while self.is_running:
            self.logger.info("Moving front")
            await self.chassis_driver.move_front(10, 1)
