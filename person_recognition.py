import json
import os
import sqlite3
from configparser import ConfigParser

import face_recognition
import numpy as np
from imutils import paths
from skimage.measure import structural_similarity as ssim

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

    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s) in the frame
        matches = face_recognition.compare_faces(
            known_faces, face_encoding, tolerance=0.60)
        name = 'Unknown'
        if True in matches:
            # save all identified names
            index_tmp = matches.index(True)
            name = names[index_tmp]

        detected_faces.append(name)

    return detected_faces


# deal with json file
def json_helper(file, mode='r', arg='', value=''):
    arg_dict = {'stranger_flag': (bool,), 'owner_in_house': (bool,)}
    try:
        # first open and read the file
        with open(file, 'r') as file_in:
            status = json.load(file_in)

        # check if arg is valid
        if arg in arg_dict:
            # read mode
            if mode == 'r':
                return status[arg]

            # write mode
            if mode == 'w':
                if isinstance(value, arg_dict[arg]):
                    status[arg] = value
                    with open(file, 'w') as file_out:
                        json.dump(status, file_out)
                else:
                    raise ValueError(arg_dict[arg])
        else:
            raise ValueError(arg_dict.keys())
    except Exception as e:
        print('Reason:', e)


# handle recognition results
def recognition_handler(result, names, status_file):
    # if a face is detected
    if result:
        # get if a owner in frame
        owner_list = [person for person in result if person in names]

        if owner_list:
            # json_helper(status_file, 'w', arg='owner_in_house', value=True)
            conn = sqlite3.connect(db_filename)
            c = conn.cursor()
            c.execute('UPDATE status_table SET owner_in_house = ? WHERE id = ?', (1, 1))
            conn.commit()
            conn.close()
        else:
            # json_helper(status_file, 'w', arg='stranger_flag', value=True)
            conn = sqlite3.connect(db_filename)
            c = conn.cursor()
            c.execute('UPDATE status_table SET stranger_flag = ? WHERE id = ?', (1, 1))
            conn.commit()
            conn.close()


def main():
    # get known face encodings
    face_encodings = [os.path.join(f, face_encoding_folder)
                      for f in sorted(os.listdir(face_encoding_folder))]
    known_faces = [np.loadtxt(f, delimiter=',') for f in face_encodings]
    names = [print(os.path.splitext(f)[0]) for f in face_encodings]

    # tmp status
    # arrive_tmp = []
    # frame_count = 0

    # initialize the first receive frame
    all_frames = sorted(os.listdir(frame_tmp))
    image_ = os.path.join(frame_tmp, all_frames[0])
    input_frame = face_recognition.load_image_file(image_)

    while True:
        # load images fron recognition_tmp
        # delete the previous frame from folder
        image_prev = image_
        input_frame_prev = input_frame
        os.remove(image_prev)

        all_frames = sorted(os.listdir(frame_tmp))
        image_ = os.path.join(frame_tmp, all_frames[0])
        input_frame = face_recognition.load_image_file(image_)

        # frame_count += 1
        # read owner status
        owner_status = json_helper(status_file, 'r', arg='owner_in_house')

        # no owner in house, start to detect stranger
        if not owner_status:
            # use ssim to compare the difference of 2 frames, to reduce computation
            diff = ssim(input_frame_prev, input_frame)
            if diff < 0.5:
                # first, detect faces in the frames
                face_result = identify_face(input_frame, known_faces, names)
                recognition_handler(face_result, names, status_file)


if __name__ == '__main__':
    main()
