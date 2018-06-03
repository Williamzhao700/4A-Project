import fcntl
import json
import os
import sqlite3
import time
from configparser import ConfigParser

import face_recognition
import numpy as np
from imutils import paths
from skimage.measure import compare_ssim
import cv2

# read the config file
cfg = ConfigParser()
cfg.read('config.cfg')
db_filename = cfg.get('person_recognition', 'db_filename')

frame_tmp = cfg.get('person_recognition', 'recognition_tmp')
face_encoding_folder = cfg.get(
    'person_recognition', 'face_encoding_folder')
status_file = cfg.get('person_recognition', 'status_file')


# identify faces in the frame
def identify_face(input_frame, known_faces, names):
    # initialize
    detected_faces = []
    face_encodings = face_recognition.face_encodings(input_frame)
    print(names)

    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s) in the frame
        matches = face_recognition.compare_faces(
            known_faces, face_encoding, tolerance=0.40)
        name = 'Unknown'
        if True in matches:
            print('!')
            # save all identified names
            index_tmp = matches.index(True)
            print(index_tmp)
            name = names[index_tmp]

        detected_faces.append(name)

    return detected_faces


# deal with json file
def json_helper(file, mode='r', arg='', value=''):
    expect_type_dict = {'stranger_flag': (bool,int), 'owner_in_house': (bool,int), 'direction':(str, ), 'action_time': (str,)}
    try:
        # first open and read the file
        with open(file, 'r') as file_in:
            fcntl.flock(file_in, fcntl.LOCK_EX)
            status = json.load(file_in)
            fcntl.flock(file_in, fcntl.LOCK_UN)

        # handle no arg
        if arg == '':
            if mode == 'r':
                return status
            else:
                raise KeyError(f"No key named '{arg}' found for write mode, only '{tuple(expect_type_dict.keys())}' are accepted")

        # check if arg is valid
        if arg in status:
            if mode == 'r':
                # read mode
                return status[arg]
            elif mode == 'w':
                # write mode
                if isinstance(value, expect_type_dict[arg]):
                    status[arg] = value
                    # print(status)
                    with open(file, 'w') as file_out:
                        fcntl.flock(file_out, fcntl.LOCK_EX)
                        # print('!')
                        json.dump(status, file_out)
                        fcntl.flock(file_out, fcntl.LOCK_UN)
                else:
                    raise ValueError(f"Expect type of arg {arg} to be one of {expect_type_dict[arg]}, got {type(arg).__name__}")
            else:
                raise ValueError(f"Invalid mode '{mode}'")
        else:
            raise KeyError(f"No key named '{arg}' found, only '{tuple(status.keys())}' are accepted")
    except Exception as e:
        print('Reason:', e)


# handle recognition results
def recognition_handler(result, names, status_file):
    # if a face is detected
    if result:
        # get if a owner in frame
        owner_list = [person for person in result if person in names]
        # print(owner_list)
        # print(names)
        # data_head = time.strftime("%Y-%m-%d %H:%M:%S")
        if owner_list:
            print('detect owner!')
            json_helper(status_file, 'w', arg='owner_in_house', value=True)
            json_helper(status_file, 'w', arg='stranger_flag', value=False)
            # conn = sqlite3.connect(db_filename)
            # c = conn.cursor()
            # c.execute('UPDATE status_table SET owner_in_house = ? WHERE id = ?', (1, 1))
            # conn.commit()
            # conn.close()
        else:
            print('stranger!')
            json_helper(status_file, 'w', arg='stranger_flag', value=True)
            # conn = sqlite3.connect(db_filename)
            # c = conn.cursor()
            # c.execute('UPDATE status_table SET stranger_flag = ? WHERE id = ?', (1, 1))
            # conn.commit()
            # conn.close()


def main():
    # get known face encodings
    face_encodings = [os.path.join(face_encoding_folder, f)
                      for f in sorted(os.listdir(face_encoding_folder))]
    known_faces = [np.loadtxt(f, delimiter=',') for f in face_encodings]
    names = [os.path.splitext(f)[0] for f in sorted(os.listdir(face_encoding_folder))]
    print(names)

    # tmp status
    # arrive_tmp = []
    # frame_count = 0

    print(time.time())

    # clear cache
    # all_frames = sorted(os.listdir(frame_tmp))
    # for frame in all_frames:
    #     os.remove(os.path.join(frame_tmp, frame))
    # time.sleep(2)

    # wait for the first receive frame
    all_frames = sorted(os.listdir(frame_tmp))
    while not all_frames:
        all_frames = sorted(os.listdir(frame_tmp))

    # print(all_frames)
    image_ = os.path.join(frame_tmp, all_frames[0])
    # print(image_)
    input_frame_tmp = cv2.imread(image_)
    
    while input_frame_tmp is None:
        # wait and retry to read the image
        time.sleep(0.5)
        input_frame_tmp = cv2.imread(image_)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    input_frame = input_frame_tmp[..., ::-1]
    input_frame_prev = input_frame
    os.remove(os.path.join(frame_tmp, all_frames[0]))
    
    while True:
        all_frames = sorted(os.listdir(frame_tmp))
        # print(all_frames[0])
        if all_frames:
            # load images fron recognition_tmp
            # delete the previous frame from folder
            time.sleep(0.5)
            image_ = os.path.join(frame_tmp, all_frames[0])
            
            input_frame_tmp = cv2.imread(image_)
            while input_frame_tmp is None:
                # wait and retry to read the image
                time.sleep(0.2)
                input_frame_tmp = cv2.imread(image_)

            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            input_frame = input_frame_tmp[..., ::-1]
            os.remove(os.path.join(frame_tmp, all_frames[0]))

            # read owner status
            owner_status = json_helper(status_file, 'r', arg='owner_in_house')
            # for debugging
            #  print(owner_status)

            # no owner in house, start to detect stranger
            if not owner_status:
                print('no owner at home')
                # use ssim to compare the difference of 2 frames, to reduce computation
                diff = compare_ssim(input_frame_prev, input_frame, multichannel=True)
                if diff < 0.8:
                    print('start to identify!')
                    # first, detect faces in the frames
                    face_result = identify_face(input_frame, known_faces, names)
                    print('identify result:')
                    print(face_result)
                    recognition_handler(face_result, names, status_file)
                else:
                    # for debug
                    # print(diff)
                    pass

            input_frame_prev = input_frame
        else:
            pass
        # time.sleep(0.6)
            # for testing
            # print('no more frames!')
        #     break



if __name__ == '__main__':
    main()
