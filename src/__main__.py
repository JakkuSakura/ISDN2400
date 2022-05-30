import logging

import tornado.ioloop

from drivers.raspberry_pi import RaspberryPiArmDriver, RaspberryPiChassisDriver
from plans.web import make_app

logger = logging.getLogger('main')
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = make_app(RaspberryPiChassisDriver(), RaspberryPiArmDriver(0))
    app.listen(8888, '0.0.0.0')
    logger.info("Listening on http://0.0.0.0:8888")
    tornado.ioloop.IOLoop.current().start()
