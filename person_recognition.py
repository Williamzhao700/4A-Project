import json
import os
from configparser import ConfigParser

import face_recognition
import numpy as np
from imutils import paths
from imutils.object_detection import non_max_suppression
from skimage.measure import structural_similarity as ssim

import cv2


# identify human in the frame
def identify_human(input_frame):
    # initialize the HOG descriptor/person detector
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    # use hog and svm
    (rects, _) = hog.detectMultiScale(input_frame, winStride=(3, 3),
            padding=(24, 24), scale=1.05)
    rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    result = non_max_suppression(rects, probs=None, overlapThresh=1)

    return (len(result))

# identify faces in the frame
def identify_face(input_frame, known_faces, names):
    # initialize
    detected_faces = []

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_frame = input_frame[:, :, ::-1]

    face_encodings = face_recognition.face_encodings(rgb_frame)

    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(known_faces, face_encoding, tolerance=0.60)
        name = 'Unknown'
        if True in matches:
            # save all identified names
            index_tmp = matches.index(True)
            name = names[index_tmp]
        
        detected_faces.append(name)
    
    return detected_faces
    

def main():
    # read the config file
    cfg = ConfigParser()
    cfg.read('config.cfg')
    frame_tmp = cfg.get('person_recognition', 'recognition_tmp')
    face_encoding_folder = cfg.get('person_recognition', 'face_encoding_folder')
    status_file = cfg.get('person_recognition', 'status_file')
    # get known face encodings
    face_encodings = [os.path.join(f, face_encoding_folder) for f in sorted(os.listdir(face_encoding_folder))]
    known_faces = [np.loadtxt(f, delimiter=',') for f in face_encodings]
    names = [print(os.path.splitext(f)[0]) for f in face_encodings]
    # tmp status
    arrive_tmp = []
    leave_tmp = 0

    # initialize the first receive frame
    all_frames = sorted(os.listdir(frame_tmp))
    image_ = os.path.join(frame_tmp, all_frames[0])
    input_frame = cv2.imread(image_)

    while True:
        # load images fron recognition_tmp
        image_prev = image_
        input_frame_prev = input_frame

        os.remove(image_prev)

        all_frames = sorted(os.listdir(frame_tmp))
        image_ = os.path.join(frame_tmp, all_frames[0])
        input_frame = cv2.imread(image_)

        # use ssim to compare the difference of 2 frames
        diff = ssim(input_frame_prev, input_frame)
        if diff < 0.5:
            # first, detect faces
            face_result = identify_face(input_frame, known_faces, names)

            # if detect faces
            if face_result:
                # no stranger
                if 'Unknown' not in face_result:
                    # increase owner number
                    incremental = [owner for owner in face_result if owner not in arrive_tmp] 
                    # open file
                    with open(status_file, 'r') as file_in:
                        status = json.load(file_in)
                    
                    status['owner_num'] += len(incremental)
                    arrive_tmp += incremental
                    # write to file
                    with open(status_file, 'w') as file_out:
                        json.dump(status, file_out)
                else:
                    # open file
                    with open(status_file, 'r') as file_in:
                        status = json.load(file_in)

                    # change status
                    status['stranger_flag'] = True
                    # write to file
                    with open(status_file, 'w') as file_out:
                        json.dump(status, file_out)                   
                    
            # if no faces detected
            else:
                # re-initialize
                arrive_tmp.clear()
                human_result = identify_human(input_frame)
                if human_result > 0:
                    # trigger a change in number
                    if human_result > leave_tmp:
                        with open(status_file, 'r') as file_in:
                            status = json.load(file_in)
                    
                        status['owner_num'] -= human_result - leave_tmp
                        # handle the fatal error of minus number in room
                        status['owner_num'] = max(status['owner_num'], 0)
                        leave_tmp = human_result

                        # write to file
                        with open(status_file, 'w') as file_out:
                            json.dump(status, file_out)
                else:
                    # re-initialize
                    leave_tmp = 0

if __name__ == '__main__':
    main()