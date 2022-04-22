import logging

import tornado.ioloop

from drivers import ArmDriver
from plans.web import make_app
logger = logging.getLogger('main')
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = make_app(ArmDriver())
    app.listen(8888)
    logger.info("Listening on http://0.0.0.0:8888")
    tornado.ioloop.IOLoop.current().start()
