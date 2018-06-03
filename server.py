import fcntl
import hashlib
import json
import logging
import os
import pickle
import secrets
import re
import sqlite3
import sys
import time
from configparser import ConfigParser

import face_recognition
import numpy as np
from flask import (Flask, Response, redirect, render_template, request,
                   session, url_for)
from imutils import paths
from imutils.object_detection import non_max_suppression
from werkzeug.utils import secure_filename

import cv2
from person_recognition import json_helper

# read the config file
cfg = ConfigParser()
cfg.read('config.cfg')

# define default video directory
video_temp = cfg.get('server', 'video_temp')
db_filename = cfg.get('server', 'db_filename')
face_upload_folder = cfg.get('server', 'face_upload_folder')
face_encoding_folder = cfg.get('server', 'face_encoding_folder')
status_file = cfg.get('server', 'status_file')
control_file = cfg.get('server', 'control_file')
recognition_tmp = cfg.get('server', 'recognition_tmp')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

# secret key, for security
secret_key = cfg.get('server', 'secret_key')
app_secret_key = cfg.get('server', 'app_secret_key')
secret_key_streaming = cfg.get('server', 'secret_key_streaming')

# initialize the status and control file
json_helper(control_file, 'w', arg='direction', value='undefined')
json_helper(control_file, 'w', arg='action_time', value='undefined')
json_helper(status_file, 'w', arg='stranger_flag', value=False)
json_helper(status_file, 'w', arg='owner_in_house', value=True)

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = app_secret_key
app.config['face_upload_folder'] = face_upload_folder
app.config['secret_key_streaming'] = secret_key_streaming

# get known face encodings
# face_encodings = [os.path.join(f, face_encoding_folder)
#                     for f in sorted(os.listdir(face_encoding_folder))]
# known_faces = [np.loadtxt(f, delimiter=',') for f in face_encodings]
# names = [print(os.path.splitext(f)[0]) for f in face_encodings]
# print('initialization')


# route http posts to this method
@app.route('/api/process', methods=['POST', 'GET'])
def frame_process():
    # define the response
    r = request.data
    # print(r)
    current_status = {'stranger_flag': False,
                      'owner_in_house': True,
                      'direction': 'undefined',
                      'action_time': 'undefined'}

    # if session.get('direction'):
    #     current_status['direction'] = session['direction']
    
    # if session.get('action_time'):
    #     current_status['action_time'] = session['action_time']

    # frame_id = request.form['frame_id']
    # print(frame_id)
    # convert string of image data to uint8
    nparr = np.fromstring(r, np.uint8)
    # decode image
    receive_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # save the file to temp folder, name with time stamp
    ct = time.time()
    data_head = time.strftime("%Y-%m-%d %H:%M:%S")
    data_secs = (ct - int(ct)) * 1000
    # high accuracy, 1 milli second
    time_stamp = "%s.%03d" % (data_head, data_secs)
    # high accuracy, 1 second
    time_stamp_low_accuracy = "%s" % data_head
    cv2.imwrite(os.path.join(video_temp, time_stamp) + '.jpg', receive_frame)
    cv2.imwrite(os.path.join(recognition_tmp, time_stamp_low_accuracy) +'.jpg', receive_frame)
    # if data_secs < 500:
    #     cv2.imwrite(os.path.join(recognition_tmp, time_stamp_low_accuracy + '-1') +'.jpg', receive_frame)
    # else:
    #     cv2.imwrite(os.path.join(recognition_tmp, time_stamp_low_accuracy + '-2') +'.jpg', receive_frame)

    status_tmp = json_helper(status_file, 'r')
    
    control_tmp = json_helper(control_file, 'r')
        
    (current_status['stranger_flag'], current_status['owner_in_house']) = (
        status_tmp['stranger_flag'], status_tmp['owner_in_house'])

    (current_status['direction'], current_status['action_time']) = (
        control_tmp['direction'], control_tmp['action_time'])

    # build a response dict to send back to client
    # response = {'message': 'image received. size={}x{}'.format(receive_frame.shape[1], receive_frame.shape[0])}
    # encode response using jsonpickle
    # with open(status_file, 'r') as f:
    #     response_ = json.load(f)

    # conn = sqlite3.connect(db_filename)
    # c = conn.cursor()
    # c.execute(
    #     'SELECT stranger_flag, owner_in_house, direction, action_time from status_table WHERE id = ?', (1, ))
    # rows = c.fetchall()
    # for row in rows:
    #     current_status[row[0]] = row[1]
    # conn.commit()
    # conn.close()
    print(current_status)
    return Response(response=json.dumps(current_status), status=200, mimetype="application/json")


# the stream page
@app.route('/stream')
def video_streaming_page():
    # check login status
    if not session.get('username'):
        return redirect('/login')

    # use dynamic token to access the video stream
    # conn = sqlite3.connect(db_filename)
    # c = conn.cursor()
    # cursor = c.execute(
    #     'SELECT token FROM users WHERE username = ?', (session['username'],))
    # token = cursor.fetchall()[0][0]
    # conn.close()
    token = app.config['secret_key_streaming']
    return render_template('stream.html', token=token)


# handle the action request
@app.route('/api/control', methods=['POST'])
def platform_control():
    # check login status
    if not session.get('username'):
        return redirect('/login')

    action = request.form['action']
    # session['direction'] = request.form['action']
    # get action time in seconds, to avoid mutiple requests in 1 second
    # session['action_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
    print(action)
    # store action into status table
    # conn = sqlite3.connect(db_filename)
    # c = conn.cursor()
    # c.execute('UPDATE status_table SET direction = ?, action_time = ? WHERE id = ?',
    #           (action, action_time, 1))
    # conn.commit()
    # conn.close()
    json_helper(control_file, 'w', arg='direction', value=action)
    json_helper(control_file, 'w', arg='action_time', value=time.strftime("%Y-%m-%d %H:%M:%S"))
    # with open(status_file, 'r') as f:
    #     status = json.load(f)
    # status['direction'] = action
    # status['action_time'] = action_time
    # with open(status_file, 'w') as f:
    #     json.dump(status, f)

    return Response(response=json.dumps({'status': session['direction']}), status=200, mimetype="application/json")


# handle the login request
@app.route('/api/login', methods=['POST'])
def login():
    username = request.form['username']
    password = hashlib.sha256(
        (request.form['password'] + secret_key).encode()).hexdigest()
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    cursor = c.execute(
        'SELECT id FROM users WHERE username = ? and password = ?', (username, password))
    # never use the following form
    # cursor = c.execute("SELECT id FROM users WHERE username = '%s' and password = '%s'" % (username, password))
    login_success = bool(cursor.fetchall())

    if login_success:
        session['username'] = username
        # new_token = secrets.token_hex(16)
        # cursor = c.execute(
        #     'UPDATE users SET token = ? WHERE username = ?', (new_token, username))
        # conn.commit()

    conn.close()

    return Response(response=json.dumps({'status': login_success}), status=200, mimetype="application/json")


@app.route('/api/logout')
def logout():
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute('UPDATE users SET token = ? WHERE username = ?',
              ('', session['username']))
    conn.commit()
    conn.close()
    session['username'] = None

    return Response(response=json.dumps({'status': True}), status=200, mimetype="application/json")


# the login page
@app.route('/login')
def login_page():
    return render_template('login.html')


# handle the register request
@app.route('/api/register', methods=['POST'])
def register():
    username = request.form['username']

    # if secrets.token_bytes(1)[0] < 300:
    #     assert 0, 'fuck'

    if not re.match('^[0-9a-zA-Z]+$', username):
        # bad username
        return Response(response=json.dumps({'status': False}), status=400, mimetype="application/json")

    password = hashlib.sha256(
        (request.form['password'] + secret_key).encode()).hexdigest()
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    cursor = c.execute('SELECT id FROM users WHERE username = ?', (username,))

    user_exists = bool(cursor.fetchall())

    # the user already exists
    if user_exists:
        conn.close()
        return Response(response=json.dumps({'status': False}), status=200, mimetype="application/json")

    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (username, password))
    conn.commit()
    conn.close()
    return Response(response=json.dumps({'status': True}), status=200, mimetype="application/json")


# define the login page
@app.route('/register')
def register_page():
    return render_template('register.html')


# handle user image upload request
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/api/upload', methods=['GET', 'POST'])
def upload_image():
    # check login status
    if not session.get('username'):
        print('fail to login!')
        return redirect('/login')
    # upload and save file
    if request.method == 'POST':
        file = request.files['image']

        if file and allowed_file(file.filename):
            # save user image
            filename = session['username'] + '.' + \
                file.filename.rsplit('.', 1)[1]
            file.save(os.path.join(app.config['face_upload_folder'], filename))
            # print(os.path.join(app.config['face_upload_folder'], filename))
            # encode the image and save the encoding result
            user_image = face_recognition.load_image_file(
                os.path.join(app.config['face_upload_folder'], filename))
            user_encoding = face_recognition.face_encodings(user_image)[0]
            if user_encoding.size != 0:
                np.savetxt(os.path.join(face_encoding_folder, filename.rsplit(
                    '.', 1)[0]) + '.txt', user_encoding, delimiter=',')
                # successfully upload the image
                return Response(response=json.dumps({'success': True}), status=200, mimetype="application/json")
            else:
                # delete the saved file
                os.remove(os.path.join(app.config['face_upload_folder'], filename))
                return Response(response=json.dumps({'success': False}), status=200, mimetype="application/json") 

    # fail to upload image
    return Response(response=json.dumps({'success': False}), status=200, mimetype="application/json")


# handle the user delete request
@app.route('/api/deleteProfile', methods=['GET'])
def delete_image():
    # check login status
    if not session.get('username'):
        print('fail to login!')
        return redirect('/login')

    filename = session['username']
    faces_list = [f for f in os.listdir(face_upload_folder)]
    face_list_without_ext = [os.path.splitext(f)[0] for f in faces_list]
    # encoding_list = [os.path.splitext(f)[0] for f in os.listdir(face_encoding_folder)]

    if filename in face_list_without_ext:
        index = face_list_without_ext.index(filename)
        os.remove(os.path.join(face_upload_folder, faces_list[index]))
        os.remove(os.path.join(face_encoding_folder, filename) + '.txt')
        return Response(response=json.dumps({'success': True}), status=200, mimetype="application/json")

    return Response(response=json.dumps({'success': False}), status=200, mimetype="application/json")


# handle the out house status
@app.route('/api/out_house', methods=['POST'])
def out_house():
    # check login status
    if not session.get('username'):
        print('fail to login!')
        return redirect('/login')
    try:
        # conn = sqlite3.connect(db_filename)
        # c = conn.cursor()
        # c.execute('UPDATE status_table SET owner_in_house = ? WHERE id = ?',
        #           (0, 1))
        # conn.commit()
        # conn.close()
        json_helper(status_file, 'w', 'owner_in_house', False)
        return Response(response=json.dumps({'success': True}), status=200, mimetype="application/json")
    except Exception as e:
        return Response(response=json.dumps({'success': False}), status=200, mimetype="application/json")

    


# handle the in house status
@app.route('/api/in_house', methods=['POST'])
def in_house():
    # check login status
    if not session.get('username'):
        print('fail to login!')
        return redirect('/login')

    try:
        # conn = sqlite3.connect(db_filename)
        # c = conn.cursor()
        # c.execute('UPDATE status_table SET owner_in_house = ? WHERE id = ?',
        #           (1, 1))
        # conn.commit()
        # conn.close()
        json_helper(status_file, 'w', 'owner_in_house', True)
        json_helper(status_file, 'w', 'stranger_flag', False)
        return Response(response=json.dumps({'success': True}), status=200, mimetype="application/json")
    except Exception as e:
        return Response(response=json.dumps({'success': False}), status=200, mimetype="application/json")


# home page
@app.route('/home')
def home_page():
    # check login status
    if not session.get('username'):
        print('fail to login!')
        return redirect('/login')

    return render_template('index.html')


# start flask app
app.run(host="0.0.0.0", port=5000)
