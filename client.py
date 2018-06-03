import json
import time

import requests

import cv2
import all_function

addr = 'http://59.78.0.136:5000'
process_url = addr + '/api/process'

# header for http request
content_type = 'image/jpeg'
headers = {'content-type': content_type}

# initialize status
# if the owner is in house
owner_flag = False
# the current people number in house
owner_number = 0
# if a stranger comes in
stranger_flag = False
last_action_time = ''
# function for frame transfer, resize it to 1/2 to speed up process


def main():
    # initialize camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 8)
    all_function.init()
    all_function.reset()
    print("\033[92mhello????????!!!!!!!!!\033[0m")
    last_action_time = ''
    # start to transfer
    while cap.isOpened():
        _, frame = cap.read()
        json_data = send_frame(frame)
        all_function.beep(json_data['stranger_flag'])
        # if json_data['stranger_flag'] == 1:
        #     all_function.beep(1)
        # else:
        #     all_function.beep(0)

        if json_data['action_time'] != last_action_time:
            last_action_time = json_data['action_time']
            print(last_action_time)
            print(json_data['direction'])
            all_function.turn(json_data['direction'])
            time.sleep(0.1)
    cap.release()
    cv2.destroyAllWindows()


def send_frame(input_frame):
    # use last action time
    global last_action_time, frame_count

    # resize to speed up
    # small_frame = cv2.resize(input_frame, dsize = (0, 0), fx=0.75, fy=0.75)
    frame_data = cv2.imencode('.jpg', input_frame)[1].tostring()
    # data_ = json.dumps({'frame_id': frame_count, 'frame_data': frame_data})
    # send http request with frame and receive response
    response = requests.post(process_url, data=frame_data, headers=headers)
    # decode response
    json_data = response.json()
    return json_data
    # for debug
    # print(json_data)


if __name__ == '__main__':
    main()
