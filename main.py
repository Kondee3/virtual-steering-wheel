import math
import time
import cv2
import mediapipe as mp
import numpy as np
from tkinter import *
from PIL import Image, ImageTk

from UDPSend import *

Send = UDPSend("192.168.4.1", 8888)

win = Tk()
win.geometry("800x600")
engine_state = False
should_draw = True

camera_from_web = None



def reload_camera():
    global camera_from_web
    camera_from_web = cv2.VideoCapture('http://192.168.4.1:81/stream')
    # camera_from_web.set(cv2.CAP_PROP_BUFFERSIZE, 1)


def turn_engine_off():
    Send.SendDataByUDPInThreadBYTE(str(0).encode())

def toggle_landmarks():
    global should_draw
    should_draw = not should_draw


def main():
    global engine_state 
    # Mediapipe
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=0,
    )
    mp_drawing = mp.solutions.drawing_utils
    middle_finger_landmark = mp_hands.HandLandmark.MIDDLE_FINGER_DIP
    index_finger_landmark = mp_hands.HandLandmark.INDEX_FINGER_TIP


    drawing_spec = mp_drawing.DrawingSpec(
        thickness=1, circle_radius=1, color=(0, 255, 0)
    )
    # CV
    cap = cv2.VideoCapture(0)
    # Tkinter
    button = Button(win, command=turn_engine_off)
    button.place(x=400, y=50)
    button.config(text="Engine OFF")
    button_draw_landmark = Button(win, command=toggle_landmarks)
    button_draw_landmark.place(x=400, y=150)
    button_reload_camera = Button(win, command=reload_camera)
    button_reload_camera.place(x=400, y=400)
    button_reload_camera.config(text="Connect with car!")
    info = Label(win)
    info.place(x=400, y=100)
    wheel_ready_lbl = Label(win)
    wheel_ready_lbl.place(x=400, y=200)
    label = Label(win)
    label.grid(row=0, column=0)
    label_esp = Label(win)
    label_esp.grid(row=1, column=0)

    is_braking = False
    prev_frame_time = 0
    new_frame_time = 0
    fps = 0

    while cap.isOpened():

        if camera_from_web is not None:
            r, f = camera_from_web.read()
            f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            image_array_esp = Image.fromarray(f)
            imgtk_esp = ImageTk.PhotoImage(image=image_array_esp)
            # label_esp.imgtk = imgtk_esp
            label_esp.configure(image=imgtk_esp)
        button_draw_landmark.config(text="Landmarks: {}".format(should_draw))
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        _data, image = cap.read()
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(image)

        hand_1 = (0, 0)
        hand_2 = (0, 0)
        l_brake_index = (0, 0)
        r_brake_index = (0, 0)
        steering_value = (0, 0)

        wheel_ready = (False, False)
        handedness = results.multi_handedness
        multi_hand_landmarks = results.multi_hand_landmarks

        if multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(multi_hand_landmarks):
                landmark = hand_landmarks.landmark[
                        middle_finger_landmark
                ]
                brake_landmark = hand_landmarks.landmark[
                        index_finger_landmark
                ]
                hand_index = handedness[idx].classification[0].index
                if should_draw:
                    mp_drawing.draw_landmarks(
                        image,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=drawing_spec,
                        connection_drawing_spec=drawing_spec,
                    )
                if hand_index == 0:
                    wheel_ready = (True, wheel_ready[1])
                    l_brake_index = (brake_landmark.x, brake_landmark.y)
                    hand_1 = (landmark.x, landmark.y)

                if hand_index == 1:
                    wheel_ready = [wheel_ready[0], True]
                    r_brake_index = (brake_landmark.x, brake_landmark.y)
                    hand_2 = (landmark.x, landmark.y)

        wheel_ready_lbl.config(text="Wheel ready: {}".format(wheel_ready))
        if all(wheel_ready):
            brake_dist = math.sqrt(
                pow(r_brake_index[1] - l_brake_index[1], 2)
                + pow(r_brake_index[0] - l_brake_index[0], 2)
            )

            if 0.075 > brake_dist > 0:
                is_braking = True
            else:  # Gaz
                is_braking = False

            deg = math.degrees(math.atan2(hand_2[1] - hand_1[1], hand_2[0] - hand_1[0]))
            abs_deg = np.clip(abs(deg / 90.0), 0.0, 1.0)
            procent = int(abs_deg * 100)
            if is_braking:
                procent = -procent

            if deg > 0:
                steering_value = (procent, 0)
                Send.SendDataByUDPInThreadBYTE(str(procent).encode())
            if deg < 0:
                steering_value = (0, procent)
                if is_braking:
                    Send.SendDataByUDPInThreadBYTE(str(procent-101).encode())
                else:
                    Send.SendDataByUDPInThreadBYTE(str(procent+101).encode())
            info.config(
                text="Prawo: {0} Lewo: {1} Hamowanie:{2} FPS:{3}".format(
                    steering_value[0], steering_value[1], is_braking, round(fps, 2)
                )
            )

        image_array = Image.fromarray(image)
        imgtk = ImageTk.PhotoImage(image=image_array.resize((320, 240)))
        # label.imgtk = imgtk
        label.configure(image=imgtk)

        win.update()

if __name__ == "__main__":
    main()
