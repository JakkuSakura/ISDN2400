import os
import sys
import logging

logger = logging.getLogger('detect')
YOLO_ROOT = os.path.abspath(os.path.join(__file__, "../../../yolov5"))
logging.basicConfig(level=logging.DEBUG)
logger.info("YOLOv5 is at %s", YOLO_ROOT)
sys.path.append(YOLO_ROOT)

import argparse
from pathlib import Path

import torch
import torch.backends.cudnn as cudnn

FILE = Path(YOLO_ROOT).resolve()
ROOT = FILE  # YOLOv5 root directory
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.datasets import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync
from utils.augmentations import letterbox
import numpy as np

weights = ROOT / 'yolov5s.pt'
device = ''  # cuda device, i.e. 0 or 0,1,2,3 or cpu
device = select_device(device)

dnn = False,  # use OpenCV DNN for ONNX inference
data = ROOT / 'data/coco128.yaml'  # dataset.yaml path
line_thickness = 3  # bounding box thickness (pixels)
hide_labels = False  # hide labels
hide_conf = False  # hide confidences
half = False  # use FP16 half-precision inference

model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)

# Load model
stride, names, pt = model.stride, model.names, model.pt
imgsz = (256, 256)  # inference size (height, width)
imgsz = check_img_size(imgsz, s=stride)  # check image size
# Run inference
model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
augment = False # augmented inference
conf_thres = 0.25 # confidence threshold
iou_thres = 0.45  # NMS IOU threshold
classes = None  # filter by class: --class 0, or --class 0 2 3
agnostic_nms = False  # class-agnostic NMS
max_det = 1000  # maximum detections per image

def process_image(x):
    img = [letterbox(x, imgsz, stride, auto=True)[0]]

    # Stack
    img = np.stack(img, 0)

    # Convert
    img = img[..., ::-1].transpose((0, 3, 1, 2))  # BGR to RGB, BHWC to BCHW
    img = np.ascontiguousarray(img)
    return img

@torch.no_grad()
def detect(im0s):
    s = ''
    im = process_image(im0s)
    im = torch.from_numpy(im).to(device)
    im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
    im /= 255  # 0 - 255 to 0.0 - 1.0
    if len(im.shape) == 3:
        im = im[None]  # expand for batch dim

    # Inference
    pred = model(im, augment=augment)
    # NMS
    pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

    assert len(pred) == 1
    # Process predictions
    for i, det in enumerate(pred):  # per image
        im0 = im0s.copy()
        s += '%gx%g ' % im.shape[2:]  # print string

        annotator = Annotator(im0, line_width=line_thickness, example=str(names))
        result = []
        if len(det):
            # Rescale boxes from img_size to im0 size
            det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()

            # Print results
            for c in det[:, -1].unique():
                n = (det[:, -1] == c).sum()  # detections per class
                s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

            # Write results
            for *xyxy, conf, cls in reversed(det):
                # Add bbox to image
                c = int(cls)  # integer class
                label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                annotator.box_label(xyxy, label, color=colors(c, True))

                result.append((xyxy, names[c]))


        # Stream results
        im0 = annotator.result()

        return im0, result
        # im0 is the result
    # Print time (inference-only)
    logger.info(f'{s}Done. ')

def main():
    video = cv2.VideoCapture(0)
    _, img = video.read()
    _, img = video.read()
    _, img = video.read()
    annotated, results = detect(img)
    print(results)


if __name__ == "__main__":
    main()
