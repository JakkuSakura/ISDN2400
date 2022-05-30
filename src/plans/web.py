import logging
import os.path
from io import BytesIO

import tornado.ioloop
import tornado.web

from drivers import ArmDriver, ChassisDriver

logger = logging.getLogger(__name__)

from PIL import Image
import sys
import math
import os
from detect import detect
import cv2
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")



class ScreenshotHandler(tornado.web.RequestHandler):
    def initialize(self, arm_driver: ArmDriver):
        self.arm_driver = arm_driver

    def get_focus_range(self, width, height, results):
        if len(results) == 0:
            return 0, 0, width, height

        x_min, y_min = width, height
        x_max, y_max = 0, 0
        for xyxy, tag in results:
            x_min = min(x_min, xyxy[0])
            y_min = min(y_min, xyxy[1])
            x_max = max(x_max, xyxy[2])
            y_max = max(y_max, xyxy[3])
        return int(x_min), int(y_min), int(x_max), int(y_max)

    async def get(self):
        image = self.arm_driver.capture_image_raw()
        annotated, results = detect(image)
        x_min, y_min, x_max, y_max = self.get_focus_range(image.shape[0], image.shape[1], results)
        logger.info("Result %s %s %s %s %s", results, x_min, y_min, x_max, y_max)
        cropped = annotated[y_min:y_max, x_min:x_max]
        # resized = cv2.resize(cropped, (360, 360))
        img = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(img)
        img_io = BytesIO()
        im_pil.save(img_io, 'JPEG', quality=50)
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

class UpgradeHandler(tornado.web.RequestHandler):
    async def post(self):
        logger.info("Upgrading")
        os.system("git pull")
        args = sys.argv[:]
        logger.info('Re-spawning %s', ' '.join(args))

        args.insert(0, sys.executable)
        self.write("Restarting")
        await self.finish()
        os.execv(sys.executable, args)

def make_app(chassis_driver: ChassisDriver, arm_driver: ArmDriver):
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
        (r"/upgrade", UpgradeHandler)

    ], **settings)


