import asyncio
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


class BackendRunnerData:
    def __init__(self):
        self.task_doc = 'Not Running'
        self.task = None

    async def submit(self, task_doc: str, task):
        if self.task is not None:
            self.task.cancel()
        logger.debug("Submitting task: %s", task_doc)
        self.task_doc = task_doc
        if task:
            async def wrapped_task():
                await task
                self.task_doc += " Done"

            self.task = asyncio.create_task(wrapped_task())


class BackendRunner(tornado.web.RequestHandler):
    def initialize(self, data: BackendRunnerData):
        self.data = data

    def get(self):
        self.write(self.data.task_doc)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class ScreenshotHandler(tornado.web.RequestHandler):
    def initialize(self, chassis_driver: ChassisDriver, arm_driver: ArmDriver, enable_detect: bool, auto_control: bool,
                   runner: BackendRunnerData):
        self.chassis_driver = chassis_driver
        self.arm_driver = arm_driver
        self.enable_detect = enable_detect
        self.runner = runner
        self.auto_control = auto_control

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

    def spray(self, results) -> bool:
        for xyxy, tag in results:
            if tag == 'person':
                logger.info("Detected person. Spraying")
                return True
        logger.info("No person detected. Not spraying")
        return False

    async def rotate_movement(self, width, results) -> bool:
        for xyxy, tag in results:
            if tag == 'person':
                center_ux = (xyxy[0] + xyxy[2]) / width
                speed = -float(center_ux * 2 - 1)
                if abs(speed) > 0.3:
                    async def rotate():
                        await self.chassis_driver.rotate(speed)
                        await asyncio.sleep(0.1)
                        await self.chassis_driver.rotate(0)

                    await self.runner.submit("Detected person. Rotating " + str(speed), rotate())
                    return True

        async def stop():
            await self.chassis_driver.rotate(0)

        await self.runner.submit("No person detected. Not rotating", stop())
        return False

    async def get(self):
        image = self.arm_driver.capture_image_raw()
        logger.debug("Captured image %sx%s", image.shape[0], image.shape[1])
        image = cv2.resize(image, (0, 0), fx=0.3, fy=0.3)
        if self.enable_detect:
            annotated, results = detect(image)
        else:
            annotated = image
            results = []
        if self.enable_detect and self.auto_control:
            spray = self.spray(results)
            if spray:
                await self.arm_driver.spray(1.0)
            else:
                await self.arm_driver.spray(0.0)
            await self.rotate_movement(annotated.shape[1], results)

        x_min, y_min, x_max, y_max = self.get_focus_range(image.shape[0], image.shape[1], results)
        logger.info("Result %s %s %s %s %s", results, x_min, y_min, x_max, y_max)
        # cropped = annotated[y_min:y_max, x_min:x_max]
        cropped = annotated
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
        await self.arm.arm(speed)
        await self.finish()


class ArmServoHandler(tornado.web.RequestHandler):
    def initialize(self, arm: ArmDriver):
        self.arm = arm

    async def post(self):
        servo = int(self.get_argument('servo'))
        speed = float(self.get_argument('speed'))
        await self.arm.servo(servo, speed)
        await self.finish()


class SprayHandler(tornado.web.RequestHandler):
    def initialize(self, arm: ArmDriver):
        self.arm = arm

    async def post(self):
        speed = float(self.get_argument('speed'))

        await self.arm.spray(speed)
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


def make_app(chassis_driver: ChassisDriver, arm_driver: ArmDriver, enable_detect=False):
    settings = {
        'template_path': os.path.join(__file__, '..', '..', '..', 'template'),
        'static_path': os.path.join(__file__, '..', '..', '..', 'static'),
    }
    runner = BackendRunnerData()

    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/screenshot", ScreenshotHandler,
         dict(chassis_driver=chassis_driver, arm_driver=arm_driver, runner=runner, enable_detect=enable_detect,
              auto_control=False)),
        (r"/move", MovementHandler, dict(chassis=chassis_driver)),
        (r"/rotate", RotationHandler, dict(chassis=chassis_driver)),
        (r"/arm", ArmVerticalHandler, dict(arm=arm_driver)),
        (r"/servo", ArmServoHandler, dict(arm=arm_driver)),
        (r'/spray', SprayHandler, dict(arm=arm_driver)),
        (r'/task', BackendRunner, dict(data=runner)),
        (r"/upgrade", UpgradeHandler)

    ], **settings)
