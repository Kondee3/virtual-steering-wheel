import math
import time
import cv2
import mediapipe as mp
import numpy as np
from tkinter import *
from PIL import Image, ImageTk
import socket


from UDPSend import *
from UDPRecv import *

Send = UDPSend("192.168.10.8", 8888)
Recv = UDPRecv("192.168.10.26", 8888)
win = Tk()
win.geometry("800x600")
is_receiving = False
engine_state = False
should_draw = True
udpWholePacket = np.array([])





def turn_engine():
    global engine_state
    engine_state = not engine_state


def toggle_landmarks():
    global should_draw
    should_draw = not should_draw


def main():
    print("Main working")
    # server = await asyncio.start_server(wait_for_data, "192.168.10.26", 8888)
    # addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    # print(f"Serving on {addrs}")
    global engine_state, udpWholePacket, is_receiving
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
    button_draw_landmark = Button(win, command=toggle_landmarks)
    button_draw_landmark.place(x=700, y=150)
    info = Label(win)
    info.place(x=700, y=100)
    wheel_ready_lbl = Label(win)
    wheel_ready_lbl.place(x=700, y=200)
    label = Label(win)
    label.grid(row=0, column=0)
    label_esp = Label(win)
    label_esp.grid(row=1, column=0)
    # Tu stworzyc labela na kamere z esp32-s3

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

        wheel_ready_lbl.config(text="Wheel ready: {}".format(wheel_ready))
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
            abs_deg = np.clip(abs(deg / 90.0), 0.0, 1.0)
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

            wartosci = "{} {}".format(steering_value[0], steering_value[1])
            Send.SendDataByUDPInThreadBYTE(wartosci.encode())
        # if not all(wheel_ready):
        #     gamepad.left_joystick_float(x_value_float=0, y_value_float=0)
        #     gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        #     gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        # gamepad.update()
        # cv2.imshow('Wirtualna kierownica', image)
        # cv2.imshow('Nowy obraz', image2)

        # Tu wstawić obraz z esp32-s3

        image_array = Image.fromarray(image)
        imgtk = ImageTk.PhotoImage(image=image_array.resize((320, 240)))
        label.imgtk = imgtk
        label.configure(image=imgtk)

        imgnp= np.asarray(bytearray(Recv.ReadRawData()), dtype=np.uint8)
        img_ln = len(imgnp)
        if img_ln:
            if img_ln == 1460 and imgnp[0] == 255 and imgnp[1] == 216 and imgnp[2] == 255:
                print("first bytes: {0}".format(imgnp.flatten()[0:2]))
                udpWholePacket = np.array(imgnp)
            elif len(udpWholePacket) > 0:
                udpWholePacket = np.append(udpWholePacket, imgnp)
                print("current len: {0}".format(img_ln))
                if img_ln != 1460 and imgnp[img_ln-2] == 255 and imgnp[img_ln-1] == 217:
                    print("end wholePacket: {0}".format(len(udpWholePacket)))
                    print(udpWholePacket)
                    imgdec = cv2.imdecode(udpWholePacket, cv2.IMREAD_COLOR)
                    if imgdec is not None:
                    # imgdec = udpWholePacket
                    # im = cv2.cvtColor(imgnp, cv2.COLOR_BGR2RGB)
                        print("show camera")
                        image_array_esp = Image.fromarray(imgdec)
                        image_array_esp.resize((320, 240))
                        imgtk_esp = ImageTk.PhotoImage(image=image_array_esp)
                        label_esp.imgtk = imgtk_esp
                        label_esp.configure(image=imgtk_esp)
            # if len(udpWholePacket) > 15000:
            #     udpWholePacket = np.array([])
        win.update()





if __name__ == "__main__":

    main()
