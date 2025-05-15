import cv2
import mediapipe as mp
import pyautogui
import threading
import time
import numpy as np 
import math
from recordv3 import CameraRecorder
import keyboard_server as ps
#import pyaudio 


###################### SET UP ######################################
width_cam, height_cam = 640, 480
mp_hand = mp.solutions.hands.Hands(False, 1, 1, 0.75, 0.5) # (static_image_mode, max_num_hands, min_detection_confidence, min_tracking_confidence, model_complexity)
cap = cv2.VideoCapture(0)
hand_status = ''
t0 = 0
t = 0

# Add these global variables
record_flag = False
recording_thread = None
last_toggle_time = 0
server = ps.KeyboardServer()
accept_thread = threading.Thread(target=server.accept_connections)
accept_thread.daemon = True
accept_thread.start()

# Add these global variables
# record_flag = False
# recording_thread = None
# last_toggle_time = 0

###################################################################
try:
    recorder = CameraRecorder()
except Exception as e:
    print(f"Error initializing audio device: {e}")
    print("Please check your microphone connection and permissions")
    exit(1)


###################################################################

def key_press(direction):
    pyautogui.press(direction)


'''
def navigate_slide(frame, x, y):
    frame_height, frame_width = frame.shape[:2]
    if x < frame_width * 0.3:
        key_press('left')
        time.sleep(1.1)
    elif x > frame_width * 0.7:
        key_press('right')
        time.sleep(1.1)
'''
def interact(frame, x, y):
    frame_height, frame_width = frame.shape[:2]
    global t0
    t = time.time()
    if t - t0 > 2: # exceed 2 seconds
        print('Exceed 2 seconds')
        t0 = time.time()
        if x < frame_width * 0.4:
            thread_sendl = threading.Thread(target=server.process_keyboard('left'))
            thread_sendl.start()
            #server.process_keyboard('left')
            #time.sleep(1.5)
        elif x > frame_width * 0.6:
            thread_sendr = threading.Thread(target=server.process_keyboard('right'))
            thread_sendr.start()
    
######################### MAIN PROCESS ################################
while True:
    success, frame = cap.read()
    frame_shape = frame.shape 
    if not success:
        break 

    frame = cv2.flip(frame, 1)

    
    # if frame_shape is None:
    #     frame_shape = frame.shape
    
    frame.flags.writeable = False 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    result = mp_hand.process(rgb_frame)



    frame.flags.writeable = True
    left_coordinate = None
    right_coordinate = None  
    left_hand_detected, right_hand_detected = False, False
    x_center, y_center = None, None
    


    if result.multi_hand_landmarks:
        for handlm, handedness in  zip(result.multi_hand_landmarks, result.multi_handedness):
            hand_label = handedness.classification[0].label
            h, w, _ = frame_shape

            cx, cy = int(handlm.landmark[8].x * w), int(handlm.landmark[8].y * h)
            if hand_label == "Left":
                left_hand_detected = True
                left_coordinate = (cx, cy)
            else: 
                right_hand_detected = True
                right_coordinate = (cx, cy)

            #----------------- Draw -----------------------#
            #cv2.circle(frame, (int(x_center), int(y_center)), 10, (255, 255, 0), -1) 
            cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

            # Hiển thị tọa độ ngón trỏ trên frame
            '''
            if left_hand_detected:
                cv2.putText(frame, f"Left Index: {left_coordinate}", (10, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            '''
            '''
            if right_hand_detected:
                cv2.putText(frame, f"Right Index: {right_coordinate}", (10, 80), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)      
              '''

            if hand_label == "Right":
                # Process right hand for slide navigation and recording control
                thumb_tip = handlm.landmark[4]
                index_tip = handlm.landmark[8]
                
                x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
                x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)
                
                cv2.circle(frame, (x_thumb, y_thumb), 10, (255, 0, 0), -1)
                cv2.circle(frame, (x_index, y_index), 10, (0, 255, 0), -1)
                
                # Check for thumb and index finger collision
                distance = math.hypot(x_thumb - x_index, y_thumb - y_index)
                if distance < 24 :
                    recorder.toggle_recording(frame)
                    cv2.circle(frame, ((x_thumb + x_index) // 2, (y_thumb + y_index) // 2), 10, (0, 255, 255), -1)

                else:
                    # If not in collision, use for slide navigation
                    interact(frame, x_index, y_index)
                

    recorder.add_frame(frame)
    cv2.imshow("Hand Frame", frame)
    key = cv2.waitKey(1)
    if key == 27:
        recorder.cleanup()
        break


cap.release()
recorder.cleanup()
cv2.destroyAllWindows()