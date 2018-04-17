import json
import logging
import pickle
import sys

import face_recognition
import numpy as np
from flask import Flask, Response, request
from imutils import paths
from imutils.object_detection import non_max_suppression

import cv2

# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# Initialize the Flask application
app = Flask(__name__)

# route http posts to this method
@app.route('/api/process', methods=['POST'])
def frame_process():
    r = request

    # convert string of image data to uint8
    nparr = np.fromstring(r.data, np.uint8)
    # decode image
    receive_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    """
    # do some fancy processing here....
    
    """

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

# start flask app
app.run(host="0.0.0.0", port=5000)
