import logging

import cv2
from drivers import ArmDriver
from PIL import Image

class RaspberryPiArmDriver(ArmDriver):
    def __init__(self, camera_id):
        self.logger = logging.getLogger(f"RaspberryPiArmDriver({camera_id})")
        self.camera = cv2.VideoCapture(camera_id)

    async def arm_up(self, distance):
        self.logger.debug('arm up %s', distance)
        pass

    async def arm_down(self, distance):
        self.logger.debug('arm down %s', distance)
        pass

    async def arm_spray(self, time):
        self.logger.debug('arm spray %s', time)
        pass

    def capture_image(self):
        self.logger.debug('capture image %s')
        return_value, image = self.camera.read()
        # You may need to convert the color.
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(img)
        return im_pil
