import json
import logging
import os
import sys
import time

import face_recognition
import numpy as np
from flask import Flask, Response, request

import cv2

# define default video directory
video_temp = './tmp/'

# Initialize the Flask application
app = Flask(__name__)

# read the latest frame
def video_gen():
    while True:
        # print("refresh all files")
        # initialize
        time.sleep(0.1)
        all_files = sorted(os.listdir(video_temp))

        with open(os.path.join(video_temp, all_files[0]), 'rb') as f:
            data = f.read()
        if len(all_files) > 5:
            os.remove(os.path.join(video_temp, all_files[0]))
        else:
            os.remove(os.path.join(video_temp, all_files[0]))
            time.sleep(0.5)
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n\r\n')

@app.route('/api/streaming')
def get_video_streaming():
    # waiting to set up initialize queue
    
    # clear cache
    all_files = sorted(os.listdir(video_temp))
    for file in all_files:
        os.remove(os.path.join(video_temp, file))
    time.sleep(1)

    return Response(video_gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# start flask app
app.run(host="0.0.0.0", port=7777)
