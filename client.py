import json
import time

import requests

import cv2
import handler

addr = 'http://192.168.1.102:5000'
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
# last action time
last_action_time = ''

# function for frame transfer, resize it to 1/2 to speed up process
def main():
    # initialize camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 15)

    print("\033[92mhello????????!!!!!!!!!\033[0m")

    # start to transfer
    while cap.isOpened():
        _, frame = cap.read()
        send_frame(frame)
            
    cap.release()
    cv2.destroyAllWindows()

def send_frame(input_frame):
    # use last action time
    global last_action_time
    # resize to speed up
    small_frame = cv2.resize(input_frame, dsize = (0, 0), fx=0.5, fy=0.5)
    frame_data = cv2.imencode('.jpg', small_frame)[1]
    # send http request with frame and receive response
    response = requests.post(process_url, data=frame_data.tostring(), headers=headers)
    # decode response
    json_data = response.json()
    handler.init(21)

    if json_data['stranger_flag']:
        handler.beep(1)
    else:
        handler.beep(0)

    if json_data['action_time'] != last_action_time:
        last_action_time = json_data['action_time']
        handler.turn1(json_data['direction'])

    # for debug
    print(json_data)

if __name__ == '__main__':
    main()
