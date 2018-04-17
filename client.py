import requests
import json
import cv2

addr = 'http://192.168.1.108:5000'
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


# function for frame transfer, resize it to 1/2 to speed up process
def frame_transfer():
    # initialize camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 15)

    print("hello")

    # start to transfer
    while(cap.isOpened()):
        _, frame = cap.read()

        # resize to speed up
        small_frame = cv2.resize(frame, dsize = (0, 0), fx=0.5, fy=0.5)
        frame_data = cv2.imencode('.jpg', small_frame)[1]

        # send http request with frame and receive response
        response = requests.post(process_url, data=frame_data.tostring(), headers=headers)
        # decode response
        json_data = json.loads(response.text)

        # for debug
        print(json_data)
        """
        if json_data['if_stranger']:
            global stranger_flag = True
        
        if json_data['if_owner']:
            global owner_flag = True
        """

    cap.release()
    cv2.destroyAllWindows()

frame_transfer()
