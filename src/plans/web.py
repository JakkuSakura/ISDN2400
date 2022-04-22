import logging
import os.path
from io import BytesIO

import tornado.ioloop
import tornado.web

from drivers import ArmDriver

logger = logging.getLogger(__name__)

from PIL import Image

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class ScreenshotHandler(tornado.web.RequestHandler):
    def initialize(self, arm_driver):
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



def make_app(driver: ArmDriver):
    settings = {
        'template_path': os.path.join(__file__, '..', '..', '..', 'template'),
        'static_path': os.path.join(__file__, '..', '..', '..', 'static'),
    }
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/screenshot", ScreenshotHandler, dict(arm_driver=driver))
    ], **settings)


