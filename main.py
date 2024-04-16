import cProfile
import re
import math
import cv2
import mediapipe as mp
import vgamepad as vg
import numpy as np

def main():
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mphands = mp.solutions.hands
    cap = cv2.VideoCapture(0)
    hands = mphands.Hands()
    gamepad = vg.VX360Gamepad()
    isbraking = False
    while cap.isOpened():
        data, image = cap.read()
        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
        results = hands.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img_h, img_w, _ = image.shape
        hand_1 = [0, 0]
        hand_2 = [0, 0]
        l_brake_index = [0, 0]
        r_brake_index = [0, 0]
        l_p = 0
        r_p = 0

        wheelReady = (False, False)
        handedness = results.multi_handedness
        multi_hand_landmarks = results.multi_hand_landmarks
        if isbraking:
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        else:
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)


        if multi_hand_landmarks:
            for idx, hand_landmarks in enumerate(multi_hand_landmarks):
                landmark = hand_landmarks.landmark[mphands.HandLandmark.MIDDLE_FINGER_DIP]
                brake_landmark = hand_landmarks.landmark[mphands.HandLandmark.INDEX_FINGER_TIP]
                hand_index = handedness[idx].classification[0].index
                mp_drawing.draw_landmarks(image, hand_landmarks, mphands.HAND_CONNECTIONS)
                if hand_index == 0:
                    wheelReady = (True, wheelReady[1])
                    l_brake_index[0] = brake_landmark.x
                    l_brake_index[1] = brake_landmark.y
                    hand_1[0] = landmark.x
                    hand_1[1] = landmark.y
                if hand_index == 1:
                    wheelReady = (wheelReady[0], True)
                    r_brake_index[0] = brake_landmark.x
                    r_brake_index[1] = brake_landmark.y
                    hand_2[0] = landmark.x
                    hand_2[1] = landmark.y
        if all(wheelReady):
            sub = math.sqrt(pow(r_brake_index[1] - l_brake_index[1], 2) + pow(r_brake_index[0] - l_brake_index[0], 2))

            if (sub < 0.075 and sub > 0):
                isbraking = True
                gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
            else:  # Gaz
                isbraking = False
                gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)

            deg = math.degrees(math.atan2(hand_2[1] - hand_1[1], hand_2[0] - hand_1[0]))
            abs_deg = np.clip(abs(deg / 90.0), 0.0, 90.0)
            procent = int(abs_deg * 100)

            if deg > 0:
                gamepad.left_joystick_float(x_value_float=abs_deg, y_value_float=0)
                r_p = procent
            if deg < 0:
                gamepad.left_joystick_float(x_value_float=-abs_deg, y_value_float=0)
                l_p = procent
            cv2.putText(image, "Lewo: {0} Prawo: {1} Hamowanie:{2}".format(l_p, r_p, isbraking), (int(0.2 * img_w), int(0.9 * img_h)),
                    cv2.FONT_HERSHEY_COMPLEX, 0.45, (255, 0, 0), 2)
        if not all(wheelReady):
            gamepad.left_joystick_float(x_value_float=0, y_value_float=0)
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
            gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        gamepad.update()
        cv2.imshow('Wirtualna kierownica', image)
        cv2.waitKey(1)
if __name__ == "__main__":
    import  pstats
    profiler = cProfile.Profile()
    profiler.enable()
    main()
    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('ncalls')
    stats.print_stats()
    
