from flask.app import Flask
from flask import Response, send_file
from drivers import ArmDriver
from typing import Optional

app = Flask("web")

driver: Optional[ArmDriver] = None


def serve_pil_image(pil_img):
    img_io = BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


@app.route('/screenshot')
def capture_image():
    image = driver and driver.capture_image()
    if image is None:
        return Response('{"error":"image not ready"}', status=503, mimetype='application/json')

    return serve_pil_image(image)


if __name__ == '__main__':
    app.run()
