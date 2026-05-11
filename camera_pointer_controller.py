import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import math
import time 

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

screen_w, screen_h = pyautogui.size()

# Primary Hand Variables
smoothening = 3
plocX, plocY = 0, 0
clocX, clocY = 0, 0
frameR = 100 

click_cooldown = 0.4      
last_click_time = 0       

pinch_start_time = 0      
hold_duration = 1.3       
is_dragging = False       

scroll_anchor_y = 0
scroll_speed = 20  # Adjust this to change how fast the page scrolls

# Secondary Hand Variables (Zoom)
zoom_anchor_y = 0
zoom_speed = 25    # Adjust for zoom pace

# NEW: The Identity Lock Variable
primary_hand_label = None 

print("CAMERA POINTER CONTROLLER ACTIVE")
print("--- PRIMARY HAND (1st Hand Detected) ---")
print("- Move: Index Finger Up")
print("- Left Click/Drag: Open Hand (Pinch Index & Thumb)")
print("- Right Click: Index + Middle + Ring Up (Pinch Ring & Thumb)")
print("- Double Click: Index + Pinky Up (Pinch Index & Thumb)")
print("- Scroll: Index + Middle Up (Joystick: Move hand Up/Down)")
print("- Volume: Shaka / Pinky Up (Move hand Left/Right)")
print("- Pause: Closed Fist")
print("--- SECONDARY HAND (2nd Hand Detected) ---")
print("- Zoom: Peace Sign Scroll with Secondory Hand ")

while True:
    success, img = cap.read()
    if not success: break
    
    img = cv2.flip(img, 1)
    cv2.rectangle(img, (frameR, frameR), (640 - frameR, 480 - frameR), (255, 0, 255), 2)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # We now zip the landmarks with the handedness (Left/Right) labels
    if results.multi_hand_landmarks and results.multi_handedness:
        
        # IDENTITY LOCK LOGIC
        # If only one hand is visible, lock its label as the Primary Hand
        if len(results.multi_hand_landmarks) == 1:
            primary_hand_label = results.multi_handedness[0].classification[0].label
        
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            
            # Check the physical label of the current hand in the loop
            current_label = handedness.classification[0].label
            
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            thumb_x, thumb_y = int(hand_landmarks.landmark[4].x * 640), int(hand_landmarks.landmark[4].y * 480)
            index_x, index_y = int(hand_landmarks.landmark[8].x * 640), int(hand_landmarks.landmark[8].y * 480)
            middle_x, middle_y = int(hand_landmarks.landmark[12].x * 640), int(hand_landmarks.landmark[12].y * 480)
            ring_x, ring_y = int(hand_landmarks.landmark[16].x * 640), int(hand_landmarks.landmark[16].y * 480)
            pinky_x, pinky_y = int(hand_landmarks.landmark[20].x * 640), int(hand_landmarks.landmark[20].y * 480)

            fingers = []
            tips = [8, 12, 16, 20] 
            for tip in tips:
                if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
                    fingers.append(1)
                else:
                    fingers.append(0)
            
            total_fingers_up = sum(fingers)
            index_thumb_dist = math.hypot(index_x - thumb_x, index_y - thumb_y)
            ring_thumb_dist = math.hypot(ring_x - thumb_x, ring_y - thumb_y)

            wrist_x = int(hand_landmarks.landmark[0].x * 640)
            wrist_y = int(hand_landmarks.landmark[0].y * 480)

            # ==========================================
            # PRIMARY HAND LOGIC
            # ==========================================
            if current_label == primary_hand_label:
                cv2.putText(img, "PRIMARY", (wrist_x - 30, wrist_y + 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
                
                # 1. CLUTCH (Closed Fist)
                if total_fingers_up == 0:
                    cv2.putText(img, "PAUSED (Clutch)", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    pinch_start_time = 0

                # 2. MOVE (Only Index Up)
                elif fingers == [1, 0, 0, 0]:
                    cv2.putText(img, "MOVING", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                    target_x = np.interp(index_x, (frameR, 640 - frameR), (0, screen_w))
                    target_y = np.interp(index_y, (frameR, 480 - frameR), (0, screen_h))
                    clocX = plocX + (target_x - plocX) / smoothening
                    clocY = plocY + (target_y - plocY) / smoothening
                    try: pyautogui.moveTo(clocX, clocY)
                    except pyautogui.FailSafeException: pass
                    plocX, plocY = clocX, clocY

                # 3. LEFT CLICK & DRAG (Open Hand)
                elif fingers == [1, 1, 1, 1]:
                    
                    if index_thumb_dist < 35:
                        cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (0, 100, 225), 3)
                        if pinch_start_time == 0: pinch_start_time = time.time()
                        elapsed_time = time.time() - pinch_start_time
                        
                        if elapsed_time >= hold_duration:
                            if not is_dragging:
                                pyautogui.mouseDown()
                                is_dragging = True
                            cv2.circle(img, (index_x, index_y), 15, (0, 0, 255), cv2.FILLED)
                            cv2.putText(img, "DRAGGING!", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                            
                            target_x = np.interp(index_x, (frameR, 640 - frameR), (0, screen_w))
                            target_y = np.interp(index_y, (frameR, 480 - frameR), (0, screen_h))
                            clocX = plocX + (target_x - plocX) / smoothening
                            clocY = plocY + (target_y - plocY) / smoothening
                            try: pyautogui.moveTo(clocX, clocY)
                            except pyautogui.FailSafeException: pass
                            plocX, plocY = clocX, clocY
                        else:
                            cv2.putText(img, "HOLDING...", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (150, 150, 150), 2)
                            angle = int((elapsed_time / hold_duration) * 360)
                            cv2.ellipse(img, (index_x, index_y), (30, 30), 0, 0, angle, (150, 150, 150), 4)
                    else:
                        if is_dragging:
                            cv2.putText(img, "DRAGGING!", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                        else:
                            cv2.putText(img, "READY TO CLICK (Frozen)", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (250, 255, 0), 2)
                        
                        if pinch_start_time != 0:
                            elapsed_time = time.time() - pinch_start_time
                            if elapsed_time < hold_duration and not is_dragging:
                                if time.time() - last_click_time > click_cooldown:
                                    cv2.circle(img, (index_x, index_y), 15, (0, 255, 0), cv2.FILLED)
                                    pyautogui.click()
                                    last_click_time = time.time()
                            pinch_start_time = 0

                # 4. CONTINUOUS JOYSTICK SCROLL (Index + Middle Up)
                elif fingers == [1, 1, 0, 0]:
                    cv2.putText(img, "SCROLL MODE", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 2)
                    
                    if scroll_anchor_y == 0:
                        scroll_anchor_y = wrist_y
                        
                    delta_y = wrist_y - scroll_anchor_y
                    deadzone = 25 
                    
                    if delta_y < -deadzone:
                        pyautogui.scroll(scroll_speed) 
                        cv2.putText(img, "SCROLLING UP ^^^", (20, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                    elif delta_y > deadzone:
                        pyautogui.scroll(-scroll_speed) 
                        cv2.putText(img, "SCROLLING DOWN vvv", (20, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    else:
                        cv2.putText(img, "(IDLE - Move Up/Down)", (20, 90), cv2.FONT_HERSHEY_PLAIN, 2, (150, 150, 150), 2)

                # 5. VOLUME SHAKA (Only Pinky Up)
                elif fingers == [0, 0, 0, 1]:
                    cv2.putText(img, "VOLUME MODE", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                    if plocX != 0:
                        vol_threshold = 15
                        delta_x = wrist_x - plocX
                        if delta_x > vol_threshold:
                            pyautogui.press('volumeup')
                            cv2.putText(img, "VOL UP >>>", (20, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                            plocX = wrist_x
                        elif delta_x < -vol_threshold:
                            pyautogui.press('volumedown')
                            cv2.putText(img, "<<< VOL DOWN", (20, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                            plocX = wrist_x
                    else:
                        plocX = wrist_x

                # 6. RIGHT CLICK
                elif fingers == [1, 1, 1, 0]:
                    cv2.putText(img, "RIGHT CLICK READY", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 165, 0), 2)
                    cv2.line(img, (thumb_x, thumb_y), (ring_x, ring_y), (255, 0, 255), 3) 
                    if ring_thumb_dist < 25:
                        cv2.circle(img, (ring_x, ring_y), 15, (0, 255, 255), cv2.FILLED) 
                        if time.time() - last_click_time > click_cooldown:
                            pyautogui.rightClick()
                            last_click_time = time.time()

                # 7. DOUBLE CLICK
                elif fingers == [1, 0, 0, 1]:
                    cv2.putText(img, "DOUBLE CLICK READY", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)
                    cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (255, 255, 0), 3)
                    if index_thumb_dist < 35:
                        cv2.circle(img, (index_x, index_y), 15, (255, 255, 0), cv2.FILLED)
                        if time.time() - last_click_time > click_cooldown:
                            pyautogui.doubleClick()
                            last_click_time = time.time()

                # GLOBAL RELEASE CHECKS FOR PRIMARY HAND
                if is_dragging and (index_thumb_dist > 60 or total_fingers_up == 0): 
                    pyautogui.mouseUp()
                    is_dragging = False
                    pinch_start_time = 0

                # Reset scroll anchor if the user drops the scroll gesture
                if fingers != [1, 1, 0, 0]:
                    scroll_anchor_y = 0


            # ==========================================
            # SECONDARY HAND LOGIC (Zooming)
            # ==========================================
            else:
                cv2.putText(img, "SECONDARY", (wrist_x - 30, wrist_y + 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 165, 0), 2)
                
                # Check for the Peace Sign (Index + Middle Up)
                if fingers == [1, 1, 0, 0]:
                    cv2.putText(img, "ZOOM MODE", (400, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                    
                    # Set the anchor when the gesture first starts
                    if zoom_anchor_y == 0:
                        zoom_anchor_y = wrist_y
                        
                    delta_y = wrist_y - zoom_anchor_y
                    deadzone = 25 
                    
                    # Hand moves UP -> Zoom OUT
                    if delta_y < -deadzone:
                        pyautogui.keyDown('ctrl')
                        pyautogui.scroll(-zoom_speed)
                        pyautogui.keyUp('ctrl')
                        cv2.putText(img, "ZOOMING OUT -", (400, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                        
                    # Hand moves DOWN -> Zoom IN
                    elif delta_y > deadzone:
                        pyautogui.keyDown('ctrl')
                        pyautogui.scroll(zoom_speed)
                        pyautogui.keyUp('ctrl')
                        cv2.putText(img, "ZOOMING IN +", (400, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                    else:
                        cv2.putText(img, "(IDLE - Move Up/Down)", (400, 90), cv2.FONT_HERSHEY_PLAIN, 2, (150, 150, 150), 2)
                else:
                    # Reset the zoom anchor when the gesture is broken
                    zoom_anchor_y = 0

    cv2.imshow("Jarvis Vision", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()