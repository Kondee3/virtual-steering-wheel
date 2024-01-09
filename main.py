import math
import cv2
import mediapipe as mp
import vgamepad as vg
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mphands = mp.solutions.hands
cap = cv2.VideoCapture(0)
hands = mphands.Hands(
    min_tracking_confidence=0.9)
gamepad = vg.VX360Gamepad()
while cap.isOpened():
    data, image = cap.read()
    image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
    results = hands.process(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img_h, img_w, _ = image.shape
    hand_1 = [0, 0] 
    hand_2 = [0, 0]
    l_p = 0
    r_p = 0
    wheelReady = (False, False)
    handedness = results.multi_handedness
    multi_hand_landmarks = results.multi_hand_landmarks
    if multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(multi_hand_landmarks):
            landmark = hand_landmarks.landmark[mphands.HandLandmark.MIDDLE_FINGER_DIP]
            hand_index = handedness[idx].classification[0].index 
            #mp_drawing.draw_landmarks(image, hand_landmarks, mphands.HAND_CONNECTIONS)
            if hand_index == 0:
                wheelReady = (True, wheelReady[1])
                hand_1[0] = landmark.x
                hand_1[1] = landmark.y
            if hand_index == 1:
                wheelReady = (wheelReady[0], True)
                hand_2[0] = landmark.x
                hand_2[1] = landmark.y
    if all(wheelReady):
        gamepad.right_trigger_float(value_float=1.0) #Gaz
        deg = math.degrees(math.atan2(hand_2[1] - hand_1[1], hand_2[0] - hand_1[0]))  
        abs_deg = np.clip(abs(deg / 90.0)*1.25, 0.0, 90.0)
        procent = int(abs_deg * 100)
        if deg > 0:
            gamepad.left_joystick_float(x_value_float=abs_deg, y_value_float=0)
            r_p = procent
        if  deg < 0:
            gamepad.left_joystick_float(x_value_float=-abs_deg, y_value_float=0)
            l_p = procent
        cv2.putText(image, "Left: {0} Right: {1}".format(l_p, r_p), (int(0.2 * img_w), int(0.9 * img_h)),
                    cv2.FONT_HERSHEY_COMPLEX, 0.35, (255, 0, 255), 1)
    if not all(wheelReady):
        gamepad.left_joystick_float(x_value_float=0, y_value_float=0)
        gamepad.right_trigger_float(value_float=0.0)
    gamepad.update()
    cv2.imshow('HandTracker', image)
    cv2.waitKey(1)
