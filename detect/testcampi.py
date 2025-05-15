import cv2
import mediapipe as mp
import pyautogui
import threading
import time
import numpy as np
import math
import keyboard_server as ps
from threading import Lock

###################### SET UP ######################################
# Camera and Mediapipe setup
width_cam, height_cam = 640, 480
mp_hand = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75,
    model_complexity=1
)

cap = cv2.VideoCapture(0)  # Open default camera
if not cap.isOpened():
    print("Error: Camera not initialized. Check connection or permissions.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Lower resolution for performance
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Recording and threading setup
hand_status = ''
prev_time = 0
record_flag = False
recording_thread = None
last_toggle_time = 0
server = ps.KeyboardServer()
lock = Lock()  # Thread safety for recording toggle

frame_counter = 0
skip_frames = 3  # Process every 3rd frame to reduce load
###################################################################

def key_press(direction):
    """Simulates a key press using pyautogui."""
    pyautogui.press(direction)

def record_screen():
    """Records the screen and saves to a file."""
    global record_flag
    try:
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fps = 30  # Adjusted for smoother recording
        out = cv2.VideoWriter('screen_recording.avi', fourcc, fps, screen_size)

        print("Recording started...")
        start_time = time.time()
        frame_count = 0

        while record_flag:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)
            frame_count += 1

            elapsed_time = time.time() - start_time
            expected_time = frame_count / fps
            if elapsed_time < expected_time:
                time.sleep(expected_time - elapsed_time)

        out.release()
        print("Recording stopped and saved.")
    except Exception as e:
        print(f"Error during screen recording: {e}")

def manage_recording():
    """Manages recording toggle on/off."""
    global record_flag, recording_thread, last_toggle_time

    current_time = time.time()
    if current_time - last_toggle_time < 1:  # Prevent rapid toggling
        return

    with lock:
        if not record_flag:
            record_flag = True
            recording_thread = threading.Thread(target=record_screen)
            recording_thread.start()
            print("Recording started")
        else:
            record_flag = False
            if recording_thread is not None:
                recording_thread.join()
            print("Recording stopped")

    last_toggle_time = current_time

def interact(frame, x, y):
    """Handles interactions based on hand position."""
    frame_height, frame_width = frame.shape[:2]
    if x < frame_width * 0.3:
        server.start('left')
        time.sleep(1.1)
    elif x > frame_width * 0.7:
        server.start('right')
        time.sleep(1.1)

######################### MAIN PROCESS ################################
try:
    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Failed to capture frame.")
            break

        frame_counter += 1
        if frame_counter % skip_frames != 0:  # Skip frames to reduce CPU load
            continue

        frame = cv2.flip(frame, 1)
        frame_shape = frame.shape
        frame.flags.writeable = False
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = mp_hand.process(rgb_frame)

        frame.flags.writeable = True
        left_coordinate = None
        right_coordinate = None
        left_hand_detected, right_hand_detected = False, False
        x_center, y_center = None, None

        if result.multi_hand_landmarks:
            for handlm, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                hand_label = handedness.classification[0].label
                h, w, _ = frame_shape

                cx, cy = int(handlm.landmark[8].x * w), int(handlm.landmark[8].y * h)
                if hand_label == "Left":
                    left_hand_detected = True
                    left_coordinate = (cx, cy)
                else:
                    right_hand_detected = True
                    right_coordinate = (cx, cy)

                # Draw hand landmarks
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

                if left_hand_detected:
                    cv2.putText(frame, f"Left Index: {left_coordinate}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                if right_hand_detected:
                    cv2.putText(frame, f"Right Index: {right_coordinate}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                if hand_label == "Right":
                    thumb_tip = handlm.landmark[4]
                    index_tip = handlm.landmark[8]

                    x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
                    x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)

                    cv2.circle(frame, (x_thumb, y_thumb), 10, (255, 0, 0), -1)
                    cv2.circle(frame, (x_index, y_index), 10, (0, 255, 0), -1)

                    distance = math.hypot(x_thumb - x_index, y_thumb - y_index)
                    if distance < 24:
                        cv2.circle(frame, ((x_thumb + x_index) // 2, (y_thumb + y_index) // 2), 10, (0, 255, 255), -1)
                        manage_recording()
                    else:
                        interact(frame, x_index, y_index)

        cv2.putText(frame, f"Recording: {'ON' if record_flag else 'OFF'}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if record_flag else (0, 0, 255), 2)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time

        cv2.putText(frame, f'FPS: {int(fps)}', (430, 35), cv2.FONT_HERSHEY_COMPLEX,
                    1, (255, 0, 255), 2)

        cv2.imshow("Hand Frame", frame)
        key = cv2.waitKey(1)
        if key == 27:  # Press Esc to exit
            break

except Exception as e:
    print(f"Error: {e}")
finally:
    if record_flag:
        record_flag = False
        if recording_thread is not None:
            recording_thread.join()
    cap.release()
    cv2.destroyAllWindows()
import cv2
import mediapipe as mp
import pyautogui
import threading
import time
import numpy as np
import math
import keyboard_server as ps
from threading import Lock

###################### SET UP ######################################
# Camera and Mediapipe setup
width_cam, height_cam = 640, 480
mp_hand = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75,
    model_complexity=1
)

cap = cv2.VideoCapture(0)  # Open default camera
if not cap.isOpened():
    print("Error: Camera not initialized. Check connection or permissions.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Lower resolution for performance
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# Recording and threading setup
hand_status = ''
prev_time = 0
record_flag = False
recording_thread = None
last_toggle_time = 0
server = ps.KeyboardServer()
lock = Lock()  # Thread safety for recording toggle

frame_counter = 0
skip_frames = 3  # Process every 3rd frame to reduce load
###################################################################

def key_press(direction):
    """Simulates a key press using pyautogui."""
    pyautogui.press(direction)

def record_screen():
    """Records the screen and saves to a file."""
    global record_flag
    try:
        screen_size = pyautogui.size()
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        fps = 30  # Adjusted for smoother recording
        out = cv2.VideoWriter('screen_recording.avi', fourcc, fps, screen_size)

        print("Recording started...")
        start_time = time.time()
        frame_count = 0

        while record_flag:
            img = pyautogui.screenshot()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            out.write(frame)
            frame_count += 1

            elapsed_time = time.time() - start_time
            expected_time = frame_count / fps
            if elapsed_time < expected_time:
                time.sleep(expected_time - elapsed_time)

        out.release()
        print("Recording stopped and saved.")
    except Exception as e:
        print(f"Error during screen recording: {e}")

def manage_recording():
    """Manages recording toggle on/off."""
    global record_flag, recording_thread, last_toggle_time

    current_time = time.time()
    if current_time - last_toggle_time < 1:  # Prevent rapid toggling
        return

    with lock:
        if not record_flag:
            record_flag = True
            recording_thread = threading.Thread(target=record_screen)
            recording_thread.start()
            print("Recording started")
        else:
            record_flag = False
            if recording_thread is not None:
                recording_thread.join()
            print("Recording stopped")

    last_toggle_time = current_time

def interact(frame, x, y):
    """Handles interactions based on hand position."""
    frame_height, frame_width = frame.shape[:2]
    if x < frame_width * 0.3:
        server.start('left')
        time.sleep(1.1)
    elif x > frame_width * 0.7:
        server.start('right')
        time.sleep(1.1)

######################### MAIN PROCESS ################################
try:
    while True:
        success, frame = cap.read()
        if not success:
            print("Error: Failed to capture frame.")
            break

        frame_counter += 1
        if frame_counter % skip_frames != 0:  # Skip frames to reduce CPU load
            continue

        frame = cv2.flip(frame, 1)
        frame_shape = frame.shape
        frame.flags.writeable = False
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = mp_hand.process(rgb_frame)

        frame.flags.writeable = True
        left_coordinate = None
        right_coordinate = None
        left_hand_detected, right_hand_detected = False, False
        x_center, y_center = None, None

        if result.multi_hand_landmarks:
            for handlm, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                hand_label = handedness.classification[0].label
                h, w, _ = frame_shape

                cx, cy = int(handlm.landmark[8].x * w), int(handlm.landmark[8].y * h)
                if hand_label == "Left":
                    left_hand_detected = True
                    left_coordinate = (cx, cy)
                else:
                    right_hand_detected = True
                    right_coordinate = (cx, cy)

                # Draw hand landmarks
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), -1)

                if left_hand_detected:
                    cv2.putText(frame, f"Left Index: {left_coordinate}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                if right_hand_detected:
                    cv2.putText(frame, f"Right Index: {right_coordinate}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                if hand_label == "Right":
                    thumb_tip = handlm.landmark[4]
                    index_tip = handlm.landmark[8]

                    x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
                    x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)

                    cv2.circle(frame, (x_thumb, y_thumb), 10, (255, 0, 0), -1)
                    cv2.circle(frame, (x_index, y_index), 10, (0, 255, 0), -1)

                    distance = math.hypot(x_thumb - x_index, y_thumb - y_index)
                    if distance < 24:
                        cv2.circle(frame, ((x_thumb + x_index) // 2, (y_thumb + y_index) // 2), 10, (0, 255, 255), -1)
                        manage_recording()
                    else:
                        interact(frame, x_index, y_index)

        cv2.putText(frame, f"Recording: {'ON' if record_flag else 'OFF'}", (10, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if record_flag else (0, 0, 255), 2)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time)
        prev_time = curr_time

        cv2.putText(frame, f'FPS: {int(fps)}', (430, 35), cv2.FONT_HERSHEY_COMPLEX,
                    1, (255, 0, 255), 2)

        cv2.imshow("Hand Frame", frame)
        key = cv2.waitKey(1)
        if key == 27:  # Press Esc to exit
            break

except Exception as e:
    print(f"Error: {e}")
finally:
    if record_flag:
        record_flag = False
        if recording_thread is not None:
            recording_thread.join()
    cap.release()
    cv2.destroyAllWindows()
