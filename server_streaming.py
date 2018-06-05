import json
import logging
import os
import sqlite3
import sys
import time
from configparser import ConfigParser

import face_recognition
import numpy as np
from flask import Flask, Response, request

import cv2

# define default video directory
video_temp = './tmp/'

cfg = ConfigParser()
cfg.read('config.cfg')
secret_key = cfg.get('server_streaming', 'secret_key')
video_temp = cfg.get('server_streaming', 'video_temp')

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

# read the latest frame
def video_gen():
    while True:
        # print("refresh all files")
        # initialize
        time.sleep(0.1)
        all_files = sorted(os.listdir(video_temp))

        if all_files:
            with open(os.path.join(video_temp, all_files[0]), 'rb') as f:
                data = f.read()
            
            os.remove(os.path.join(video_temp, all_files[0]))
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n\r\n')   
        else:
            time.sleep(0.5)
            

@app.route('/api/streaming')
def get_video_streaming():
    # waiting to set up initialize queue
    token = request.args.get('token', '')

    # handle empty and invalid token
    if not token:
        return Response(response="Missing token!", status=400)
    
    if not token == app.secret_key:
        return Response(response="Invalid token!!!", status=400)

    # clear cache
    all_files = sorted(os.listdir(video_temp))
    for file in all_files:
        os.remove(os.path.join(video_temp, file))
    time.sleep(1)

    return Response(video_gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# start flask app
app.run(host="0.0.0.0", port=7777)
