import logging
import sys
import time
from logging import exception
from threading import Condition, Thread
# from ultralytics import YOLO

import cv2
import numpy as np
import requests
from cscore import CameraServer
from networktables import NetworkTables
import torch

# Camera Settings
width, height = 960, 540
camera = CameraServer.startAutomaticCapture()
camera.setFPS(10)
camera.setResolution(width, height)
input_stream = CameraServer.getVideo()
output_stream = CameraServer.putVideo('Vision', width, height)


# Templates
clean_img = np.zeros(shape=(width, height, 3), dtype=np.uint8)
kernel = np.ones((5, 5), np.uint8)


# Connection Parameters
ROBOT_IP = 'http://10.56.35.2'
smart_dashboard = None
CALIBRATION_PORT = 'tower'


# Color Range
min_hsv = np.array((60, 255, 77))
max_hsv = np.array((78, 255, 133))


# Hardare Parameters
camera_view_angle = 50

# model = YOLO('yolov8n.pt')

def process_image(frame):
    print("4")
    # with torch.no_grad():
    #     results = model(frame)
    # for r in results:
    #     for b in r.boxes:
    #         print (b)
    x = 5
    y =6

    return x, y


def put_number(key, number):
    if smart_dashboard:
        smart_dashboard.putNumber(key, number)

def put_boolean(key, value):
    if smart_dashboard:
        smart_dashboard.putBoolean(key, value)


def init_smart_dashboard():
    if not smart_dashboard:
        return
    smart_dashboard.putNumber('calibration-lower-h-' + CALIBRATION_PORT, min_hsv[0])
    smart_dashboard.putNumber('calibration-lower-s-' + CALIBRATION_PORT, min_hsv[1])
    smart_dashboard.putNumber('calibration-lower-v-' + CALIBRATION_PORT, min_hsv[2])
    smart_dashboard.putNumber('calibration-upper-h-' + CALIBRATION_PORT, max_hsv[0])
    smart_dashboard.putNumber('calibration-upper-s-' + CALIBRATION_PORT, max_hsv[1])
    smart_dashboard.putNumber('calibration-upper-v-' + CALIBRATION_PORT, max_hsv[2])
    smart_dashboard.putNumber('camera_view_angle' + CALIBRATION_PORT, camera_view_angle)


def update_vars():
    if not smart_dashboard: return

    global camera_view_angle

    min_hsv[0] = smart_dashboard.getNumber('calibration-lower-h-' + CALIBRATION_PORT, min_hsv[0])
    min_hsv[1] = smart_dashboard.getNumber('calibration-lower-s-' + CALIBRATION_PORT, min_hsv[1])
    min_hsv[2] = smart_dashboard.getNumber('calibration-lower-v-' + CALIBRATION_PORT, min_hsv[2])

    max_hsv[0] = smart_dashboard.getNumber('calibration-upper-h-' + CALIBRATION_PORT, max_hsv[0])
    max_hsv[1] = smart_dashboard.getNumber('calibration-upper-s-' + CALIBRATION_PORT, max_hsv[1])
    max_hsv[2] = smart_dashboard.getNumber('calibration-upper-v-' + CALIBRATION_PORT, max_hsv[2])
    camera_view_angle = smart_dashboard.getNumber('camera_view_angle' + CALIBRATION_PORT, camera_view_angle)


def connect():
    global smart_dashboard
    cond = Condition()
    notified = False
    NetworkTables.initialize(server='10.56.35.2')
    NetworkTables.addConnectionListener(lambda connected, info: connection_listener(connected, info, cond), immediateNotify=True)

    with cond:
        logging.info("Connecting...")
        if not notified:
            cond.wait()

    logging.info("Connected!")
    smart_dashboard = NetworkTables.getTable('SmartDashboard')
    update_vars()
    init_smart_dashboard()
    smart_dashboard.addEntryListener(lambda source, key, value, isNew : update_vars())


def connection_listener(connected, info, cond : Condition):
    logging.info("{info}; Connceted={status}".format(info = info, status = connected))
    with cond:
        cond.notify()


def connect_periodically(on_connect = None):
    while not connected_to_robot():
        time.sleep(10)
    connect()
    if on_connect:
        on_connect()


def start_connection(on_connect = None):
    thread = Thread(target=lambda : connect_periodically(on_connect))
    thread.start()

def connected_to_robot():
    try:
        logging.info("Searching for robot...")
        status_code = requests.get(ROBOT_IP, timeout=(2, 1)).status_code
        logging.info(status_code)
        return status_code == 200
    except exception as e:
        logging.warning(e)
        logging.warning('robot is dead 🦀')
        return False

print("2")
if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    print("1")
    # start_connection()

    while True:
        print("3")
        time, frame = input_stream.grabFrame(clean_img)

        if time == 0:
            continue

        x, y = process_image(frame)

        if x and y is not None:
            put_number('vision_tower_x', x)
            put_number('vision_tower_y', y)
            put_boolean('vision_found', True)
        else:
            put_boolean('vision_found', False)