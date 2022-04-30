import logging
import os.path
from io import BytesIO

import tornado.ioloop
import tornado.web

from drivers import ArmDriver, ChassisDriver

logger = logging.getLogger(__name__)

from PIL import Image
import math


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class ScreenshotHandler(tornado.web.RequestHandler):
    def initialize(self, arm_driver: ArmDriver):
        self.arm_driver = arm_driver

    async def get(self):
        img_io = BytesIO()
        image = self.arm_driver.capture_image()
        if not image:
            image = Image.new('RGB', (600, 400))

        image.save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        self.set_header("Content-type", "image/jpeg")
        self.write(img_io.read())
        await self.finish()


class MovementHandler(tornado.web.RequestHandler):
    def initialize(self, chassis: ChassisDriver):
        self.chassis = chassis

    async def post(self):
        udx = float(self.get_argument('udx'))
        udy = float(self.get_argument('udy'))
        # up is 0, positive is counterclockwise
        angle = math.atan2(-udx, udy)
        length = math.sqrt(udx * udx + udy * udy)
        await self.chassis.move(angle, length)
        await self.finish()


class RotationHandler(tornado.web.RequestHandler):
    def initialize(self, chassis: ChassisDriver):
        self.chassis = chassis

    async def post(self):
        speed = float(self.get_argument('speed'))
        await self.chassis.rotate(speed)
        await self.finish()


class ArmVerticalHandler(tornado.web.RequestHandler):
    def initialize(self, arm: ArmDriver):
        self.arm = arm

    async def post(self):
        speed = float(self.get_argument('speed'))
        await self.arm.arm_up(speed)
        await self.finish()


def make_app(arm_driver: ArmDriver, chassis_driver: ChassisDriver):
    settings = {
        'template_path': os.path.join(__file__, '..', '..', '..', 'template'),
        'static_path': os.path.join(__file__, '..', '..', '..', 'static'),
    }
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/screenshot", ScreenshotHandler, dict(arm_driver=arm_driver)),
        (r"/move", MovementHandler, dict(chassis=chassis_driver)),
        (r"/rotate", RotationHandler, dict(chassis=chassis_driver)),
        (r"/arm", ArmVerticalHandler, dict(arm=arm_driver)),

    ], **settings)
