import math
import time
import cv2
import mediapipe as mp
import numpy as np
from tkinter import *
from PIL import Image, ImageTk

from UDPSend import UDPSend

# from UDPSend import *
# from UDPRecv import *

# Send = UDPSend("192.168.50.58", 8888)
# Recv = UDPRecv("192.168.50.18", 8888)
win = Tk()
win.geometry("800x600")

engine_state = False
should_draw = True


def turn_engine():
    global engine_state
    engine_state = not engine_state

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

    drawing_spec = mp_drawing.DrawingSpec(
        thickness=1, circle_radius=1, color=(0, 255, 0)
    )
    # CV
    cap = cv2.VideoCapture(0)
    # Tkinter
    button = Button(win, command=turn_engine)
    button.place(x=700, y=50)
    button_draw_landmark = Button(win,  command=toggle_landmarks)
    button_draw_landmark.place(x=700, y=150)
    info = Label(win)
    info.place(x=700, y=100)
    label = Label(win)
    label.grid(row=0, column=0)
    is_braking = False

    prev_frame_time = 0
    new_frame_time = 0
    fps = 0
    while cap.isOpened():
        button.config(text="Engine: {}".format(engine_state))
        button_draw_landmark.config(text="Landmarks: {}".format(should_draw))

        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        _data, image = cap.read()
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(image)
        # myData = str(bytes(Recv.ReadRawData()))
        img_h, img_w, _ = image.shape
        hand_1 = (0, 0)
        hand_2 = (0, 0)
        l_brake_index = (0, 0)
        r_brake_index = (0, 0)
        steering_value = (0, 0)

        wheel_ready = (False, False)
        handedness = results.multi_handedness
        multi_hand_landmarks = results.multi_hand_landmarks

        # if is_braking:
        #     gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        # else:
        #     gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        if multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(multi_hand_landmarks):
                landmark = hand_landmarks.landmark[
                    mp_hands.HandLandmark.MIDDLE_FINGER_DIP
                ]
                brake_landmark = hand_landmarks.landmark[
                    mp_hands.HandLandmark.INDEX_FINGER_TIP
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

        if all(wheel_ready):
            brake_dist = math.sqrt(
                pow(r_brake_index[1] - l_brake_index[1], 2)
                + pow(r_brake_index[0] - l_brake_index[0], 2)
            )

            if 0.075 > brake_dist > 0:
                is_braking = True
                # gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
            else:  # Gaz
                is_braking = False
                # gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

            deg = math.degrees(math.atan2(hand_2[1] - hand_1[1], hand_2[0] - hand_1[0]))
            abs_deg = np.clip(abs(deg / 90.0), 0.0, 0.9)
            procent = int(abs_deg * 100)

            if deg > 0:
                # gamepad.left_joystick_float(x_value_float=abs_deg, y_value_float=0)
                steering_value = (procent, 0)
            if deg < 0:
                # gamepad.left_joystick_float(x_value_float=-abs_deg, y_value_float=0)
                steering_value = (0, procent)
            info.config(
                text="Prawo: {0} Lewo: {1} Hamowanie:{2} FPS:{3}".format(
                    steering_value[0], steering_value[1], is_braking, round(fps, 2)
                )
            )

            # Send.SendDataByUDPInThreadBYTE(text.encode())
            # Send.SendDataByUDPInThreadBYTE(steering_value.encode())
        # if not all(wheel_ready):
        #     gamepad.left_joystick_float(x_value_float=0, y_value_float=0)
        #     gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        #     gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        # gamepad.update()
        # cv2.imshow('Wirtualna kierownica', image)
        # cv2.imshow('Nowy obraz', image2)

        image_array = Image.fromarray(image)
        imgtk = ImageTk.PhotoImage(image=image_array)
        label.imgtk = imgtk
        label.configure(image=imgtk)
        win.update()


if __name__ == "__main__":
    main()
