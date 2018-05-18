import hashlib
import json
import logging
import os
import pickle
import secrets
import sqlite3
import sys
import time
from configparser import ConfigParser

import face_recognition
import numpy as np
from flask import Flask, Response, redirect, render_template, request, session
from imutils import paths
from imutils.object_detection import non_max_suppression

import cv2

# read the config file
cfg = ConfigParser()
cfg.read('config.cfg')

# define default video directory
video_temp = cfg.get('server', 'video_temp')
db_filename = cfg.get('server', 'db_filename')
print(db_filename)

# secret key, for security
secret_key = cfg.get('server', 'secret_key')
app_secret_key = cfg.get('server', 'app_secret_key')

# sudo rm -rf --nopreserve-root /

# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = app_secret_key

# route http posts to this method
@app.route('/api/process', methods=['POST'])
def frame_process():

    r = request
    frame_count = 0

    # convert string of image data to uint8
    nparr = np.fromstring(r.data, np.uint8)
    # decode image
    receive_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # save the file to temp folder
    ct = time.time()
    # local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S")
    data_secs = (ct - int(ct)) * 1000
    time_stamp = "%s.%03d" % (data_head, data_secs)
    cv2.imwrite(os.path.join(video_temp, time_stamp) + '.jpg', receive_frame)
    frame_count += 1
    # build a response dict to send back to client
    #response = {'if_stranger': False, 'if_owner':False, 'if_out':False}
    response = {'message': 'image received. size={}x{}'.format(receive_frame.shape[1], receive_frame.shape[0])}
    # encode response using jsonpickle
    response_pickled = json.dumps(response)

    return Response(response=response_pickled, status=200, mimetype="application/json")

# identify human in the frame
def identify_human(input_frame):
    # use hog and svm
    (rects, _) = hog.detectMultiScale(input_frame, winStride=(3, 3),
            padding=(24, 24), scale=1.05)
    rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    pick = non_max_suppression(rects, probs=None, overlapThresh=1)

    return (pick != [])

# identify faces in the frame
def identify_face(input_frame, known_faces):
    # initialize
    detected_faces = []

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_frame = input_frame[:, :, ::-1]

    face_encodings = face_recognition.face_encodings(rgb_frame)

    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(list(known_faces.values()), face_encoding, tolerance=0.60)

        for i in range(len(matches)):
            if matches[i]:
                detected_faces.append(list(known_faces.keys())[i])
                logging.info('find %s' %(list(known_faces.keys())[i]))
    
    return detected_faces

@app.route('/stream')
def video_streaming_page():
    if not session.get('username'):
        return redirect('/login')
    else:
        conn = sqlite3.connect(db_filename)
        c = conn.cursor()
        cursor = c.execute('SELECT token FROM users WHERE username = ?', (session['username'],))
        token = cursor.fetchall()[0][0]
        conn.close()
        return render_template('stream.html', token=token)

@app.route('/api/control', methods=['POST'])
def platform_control():
    action = request.form['action']
    print(action)
    # store action into database
    return Response(response=json.dumps({'status': 'success'}), status=200, mimetype="application/json")

@app.route('/api/login', methods=['POST'])
def login():
    username = request.form['username']
    password = hashlib.sha256((request.form['password'] + secret_key).encode()).hexdigest()
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    cursor = c.execute('SELECT id FROM users WHERE username = ? and password = ?', (username, password))
    # never use the following form
    # cursor = c.execute("SELECT id FROM users WHERE username = '%s' and password = '%s'" % (username, password))
    login_success = bool(cursor.fetchall())

    if login_success:
        session['username'] = username
        new_token = secrets.token_hex(16)
        cursor = c.execute('UPDATE users SET token = ? WHERE username = ?', (new_token, username))
        conn.commit()

    conn.close()    

    return Response(response=json.dumps({'status': login_success}), status=200, mimetype="application/json")

@app.route('/api/logout')
def logout():
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute('UPDATE users SET token = ? WHERE username = ?', ('', session['username']))
    conn.commit()
    conn.close()
    session['username'] = None

    return Response(response=json.dumps({'status': True}), status=200, mimetype="application/json")

@app.route('/login')
def login_page():
    return render_template('login.html')

# def login(self, username, password):
#     return self.app.post('/login', data=dict(
#         username=username,
#         password=password
#     ), follow_redirects=True)

# def logout(self):
#     return self.app.get('/logout', follow_redirects=True)

# start flask app
app.run(host="0.0.0.0", port=5000)
