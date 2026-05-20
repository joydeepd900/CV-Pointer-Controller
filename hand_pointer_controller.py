"""
Hand Pointer-Controller
--------------------------------------
A computer vision-based virtual mouse controller using MediaPipe and PyAutoGUI.
Features include adaptive smoothing (One Euro Filter), asynchronous video capture
for zero hardware latency, and multi-hand gesture recognition for cursor control,
scrolling, zooming, and volume adjustments.
"""

import cv2
import mediapipe as mp
import pyautogui
import threading
import numpy as np
import math
import time 

# ==========================================
# UTILITY CLASSES
# ==========================================

class OneEuroFilter:
    """
    An adaptive low-pass filter for noisy data.
    Eliminates jitter at low speeds (heavy smoothing) and reduces lag at high 
    speeds (low smoothing) by dynamically calculating the cutoff frequency based 
    on the rate of change (velocity).
    """
    def __init__(self, mincutoff=1.0, beta=0.007, dcutoff=1.0):
        self.mincutoff = mincutoff
        self.beta = beta
        self.dcutoff = dcutoff
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    def smoothing_factor(self, cutoff, dt):
        """Calculates the smoothing factor (alpha) for the low-pass filter."""
        r = 2 * math.pi * cutoff * dt
        return r / (r + 1)

    def __call__(self, x, t=None):
        """Applies the filter to the incoming data point 'x'."""
        if t is None: t = time.time()
        if self.t_prev is None:
            self.x_prev = x
            self.t_prev = t
            return x

        dt = t - self.t_prev
        if dt <= 0: return x

        # Filter the velocity
        dx = (x - self.x_prev) / dt
        alpha_d = self.smoothing_factor(self.dcutoff, dt)
        dx_hat = alpha_d * dx + (1 - alpha_d) * self.dx_prev

        # Filter the position dynamically
        cutoff = self.mincutoff + self.beta * abs(dx_hat)
        alpha_x = self.smoothing_factor(cutoff, dt)
        x_hat = alpha_x * x + (1 - alpha_x) * self.x_prev

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        
        return x_hat

class VideoStream:
    """
    Asynchronous video capture mechanism.
    Reads frames from the webcam in a dedicated background thread to prevent 
    camera I/O bottlenecks from slowing down the main computer vision processing loop.
    """
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        # Daemon thread ensures it closes when the main program exits
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                self.stream.release()
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.grabbed, self.frame

    def stop(self):
        self.stopped = True

# ==========================================
# SYSTEM INITIALIZATION
# ==========================================

# Configure PyAutoGUI to eliminate artificial delays and corner-crash aborts
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# Initialize MediaPipe Hands solution
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Start threaded video stream
cap = VideoStream(0).start()

# System screen dimensions for coordinate mapping
screen_w, screen_h = pyautogui.size()

# Region of Interest (ROI): The physical webcam area mapped to the screen
# Leaves space at the bottom to ensure the wrist remains in the frame
pt1_x, pt1_y = 100, 50   
pt2_x, pt2_y = 540, 350  

# ==========================================
# STATE VARIABLES
# ==========================================

# Primary Hand State (Cursor, Clicking, Scrolling, Volume)
clocX, clocY = 0, 0
click_cooldown = 0.4      
last_click_time = 0       

pinch_start_time = 0      
hold_duration = 1.3       
is_dragging = False       

scroll_anchor_y = 0
scroll_speed = 20  

vol_anchor_x = 0 

# Secondary Hand State (Zooming)
zoom_anchor_y = 0
zoom_speed = 25    

# Identity Lock: Ensures primary hand controls remain consistent even if crossed
primary_hand_label = None 

# Initialize coordinate smoothers
filter_x = OneEuroFilter(mincutoff=0.2, beta=0.075)
filter_y = OneEuroFilter(mincutoff=0.2, beta=0.075)

# ==========================================
# STARTUP LOG
# ==========================================
print("HAND POINTER CONTROLLER ACTIVE")
print("Press 'q' to quit")
print("=======================================")
print("--- PRIMARY HAND (1st Hand Detected) ---")
print("- Move: Index Finger Up")
print("- Left Click/Drag: Open Hand, then Pinch Index & Thumb (Hold for Drag)")
print("- Right Click: Index + Middle + Ring Up, then Pinch Ring & Thumb for Click")
print("- Double Click: Index + Pinky Up, then Pinch Index & Thumb for Click")
print("- Scroll: Index + Middle Up (Joystick: Move hand Up/Down)")
print("- Volume: Shaka / Thumb + Pinky Up (Move hand Left/Right)")
print("- Pause: Closed Fist")
print("--- SECONDARY HAND (2nd Hand Detected) ---")
print("- Zoom: Peace Sign Scroll with Secondary Hand ")
print("=======================================")

# ==========================================
# MAIN TRACKING LOOP
# ==========================================

while True:
    success, img = cap.read()
    if not success: break
    
    # Mirror image for intuitive control and draw ROI
    img = cv2.flip(img, 1)

    # MediaPipe requires RGB images
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # Draw the ROI AFTER processing so it doesn't interfere with the AI's vision
    cv2.rectangle(img, (pt1_x, pt1_y), (pt2_x, pt2_y), (255, 0, 255), 2)

    # Verify both landmarks and handedness labels are present
    if results.multi_hand_landmarks and results.multi_handedness:
        
        # Lock the first detected hand as 'Primary' to prevent swapping issues
        if len(results.multi_hand_landmarks) == 1:
            primary_hand_label = results.multi_handedness[0].classification[0].label
        
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            current_label = handedness.classification[0].label
            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Extract key landmark coordinates
            thumb_x, thumb_y = int(hand_landmarks.landmark[4].x * 640), int(hand_landmarks.landmark[4].y * 480)
            index_x, index_y = int(hand_landmarks.landmark[8].x * 640), int(hand_landmarks.landmark[8].y * 480)
            middle_x, middle_y = int(hand_landmarks.landmark[12].x * 640), int(hand_landmarks.landmark[12].y * 480)
            ring_x, ring_y = int(hand_landmarks.landmark[16].x * 640), int(hand_landmarks.landmark[16].y * 480)
            pinky_x, pinky_y = int(hand_landmarks.landmark[20].x * 640), int(hand_landmarks.landmark[20].y * 480)

            # Determine which fingers are extended (1 = up, 0 = down)
            fingers = []
            tips = [8, 12, 16, 20] 
            for tip in tips:
                if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
                    fingers.append(1)
                else:
                    fingers.append(0)
            
            total_fingers_up = sum(fingers)
            
            # Calculate Euclidean distances for pinch gestures
            index_thumb_dist = math.hypot(index_x - thumb_x, index_y - thumb_y)
            ring_thumb_dist = math.hypot(ring_x - thumb_x, ring_y - thumb_y)

            # Wrist serves as the anchor point for gesture joysticks (scroll/volume)
            wrist_x = int(hand_landmarks.landmark[0].x * 640)
            wrist_y = int(hand_landmarks.landmark[0].y * 480)

            # ------------------------------------------
            # PRIMARY HAND CONTROLS
            # ------------------------------------------
            if current_label == primary_hand_label:
                cv2.putText(img, "PRIMARY", (wrist_x - 30, wrist_y + 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 0), 2)
                
                # 1. CLUTCH (Closed Fist) - Halts all inputs
                if total_fingers_up == 0:
                    cv2.putText(img, "PAUSED (Clutch)", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    pinch_start_time = 0

                # 2. MOVE (Only Index Extended)
                elif fingers == [1, 0, 0, 0]:
                    cv2.putText(img, "MOVING", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                    
                    # Map webcam ROI coordinates to physical screen dimensions
                    target_x = np.interp(index_x, (pt1_x, pt2_x), (0, screen_w))
                    target_y = np.interp(index_y, (pt1_y, pt2_y), (0, screen_h))
                    
                    # Apply One Euro filtering for smooth cursor interpolation
                    clocX = filter_x(target_x)
                    clocY = filter_y(target_y)
                    
                    try: pyautogui.moveTo(clocX, clocY)
                    except pyautogui.FailSafeException: pass

                # 3. LEFT CLICK & DRAG (All Fingers Extended, Pinch Index & Thumb)
                elif fingers[1:] == [1, 1, 1]:
                    
                    # Maintain cursor movement if actively dragging
                    if is_dragging:
                        cv2.circle(img, (index_x, index_y), 15, (0, 0, 255), cv2.FILLED)
                        cv2.putText(img, "DRAGGING!", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                        
                        target_x = np.interp(index_x, (pt1_x, pt2_x), (0, screen_w))
                        target_y = np.interp(index_y, (pt1_y, pt2_y), (0, screen_h))
                        clocX = filter_x(target_x)
                        clocY = filter_y(target_y)
                        
                        try: pyautogui.moveTo(clocX, clocY)
                        except pyautogui.FailSafeException: pass
                    
                    # Initiate drag hold-timer upon tight pinch
                    elif index_thumb_dist < 35:
                        cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (0, 100, 225), 3)
                        if pinch_start_time == 0: pinch_start_time = time.time()
                        elapsed_time = time.time() - pinch_start_time
                        
                        if elapsed_time >= hold_duration:
                            pyautogui.mouseDown()
                            is_dragging = True
                            pinch_start_time = 0
                        else:
                            cv2.putText(img, "HOLDING...", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (150, 150, 150), 2)
                            angle = int((elapsed_time / hold_duration) * 360)
                            cv2.ellipse(img, (index_x, index_y), (30, 30), 0, 0, angle, (150, 150, 150), 4)
                            
                    # Standard Left Click execution if pinch released before hold threshold
                    else:
                        cv2.putText(img, "READY TO CLICK (Frozen)", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (250, 255, 0), 2)
                        if pinch_start_time != 0:
                            elapsed_time = time.time() - pinch_start_time
                            if elapsed_time < hold_duration:
                                if time.time() - last_click_time > click_cooldown:
                                    cv2.circle(img, (index_x, index_y), 15, (0, 255, 0), cv2.FILLED)
                                    pyautogui.click()
                                    last_click_time = time.time()
                            pinch_start_time = 0

                # 4. JOYSTICK SCROLL (Index & Middle Extended)
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

                # 5. VOLUME SHAKA (Only Pinky Extended)
                elif fingers == [0, 0, 0, 1]:
                    cv2.putText(img, "VOLUME MODE", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
                    
                    if vol_anchor_x == 0:
                        vol_anchor_x = wrist_x
                        
                    vol_threshold = 15
                    delta_x = wrist_x - vol_anchor_x
                    
                    if delta_x > vol_threshold:
                        pyautogui.press('volumeup')
                        cv2.putText(img, "VOL UP >>>", (20, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                        vol_anchor_x = wrist_x
                    elif delta_x < -vol_threshold:
                        pyautogui.press('volumedown')
                        cv2.putText(img, "<<< VOL DOWN", (20, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                        vol_anchor_x = wrist_x

                # 6. RIGHT CLICK (Index, Middle, Ring Extended; Pinch Ring & Thumb)
                elif fingers[0] == 1 and fingers[1] == 1 and fingers[3] == 0:
                    cv2.putText(img, "RIGHT CLICK READY", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 165, 0), 2)
                    cv2.line(img, (thumb_x, thumb_y), (ring_x, ring_y), (255, 0, 255), 3) 
                    
                    if ring_thumb_dist < 25:
                        cv2.circle(img, (ring_x, ring_y), 15, (0, 255, 255), cv2.FILLED) 
                        if time.time() - last_click_time > click_cooldown:
                            pyautogui.rightClick()
                            last_click_time = time.time()

                # 7. DOUBLE CLICK (Index & Pinky Extended; Pinch Index & Thumb)
                elif fingers[1:] == [0, 0, 1]:
                    cv2.putText(img, "DOUBLE CLICK READY", (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 2)
                    cv2.line(img, (thumb_x, thumb_y), (index_x, index_y), (255, 255, 0), 3)
                    
                    if index_thumb_dist < 35:
                        cv2.circle(img, (index_x, index_y), 15, (255, 255, 0), cv2.FILLED)
                        if time.time() - last_click_time > click_cooldown:
                            pyautogui.doubleClick()
                            last_click_time = time.time()

                # ------------------------------------------
                # STATE RESETS & FAILSAFES (Primary Hand)
                # ------------------------------------------
                
                # Release mouse drag if pinch is broken or hand closes
                if is_dragging and (index_thumb_dist > 60 or total_fingers_up == 0): 
                    pyautogui.mouseUp()
                    is_dragging = False
                    pinch_start_time = 0

                # Clear joystick anchors when gestures are broken
                if fingers != [1, 1, 0, 0]: scroll_anchor_y = 0
                if fingers != [0, 0, 0, 1]: vol_anchor_x = 0

            # ------------------------------------------
            # SECONDARY HAND CONTROLS (Zooming)
            # ------------------------------------------
            else:
                cv2.putText(img, "SECONDARY", (wrist_x - 30, wrist_y + 30), cv2.FONT_HERSHEY_PLAIN, 1.5, (255, 165, 0), 2)
                
                # Check for Peace Sign posture
                if fingers == [1, 1, 0, 0]:
                    cv2.putText(img, "ZOOM MODE", (400, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                    
                    if zoom_anchor_y == 0:
                        zoom_anchor_y = wrist_y
                        
                    delta_y = wrist_y - zoom_anchor_y
                    deadzone = 25 
                    
                    # Upward movement -> Zoom Out
                    if delta_y < -deadzone:
                        pyautogui.keyDown('ctrl')
                        pyautogui.scroll(-zoom_speed)
                        pyautogui.keyUp('ctrl')
                        cv2.putText(img, "ZOOMING OUT -", (400, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                        
                    # Downward movement -> Zoom In
                    elif delta_y > deadzone:
                        pyautogui.keyDown('ctrl')
                        pyautogui.scroll(zoom_speed)
                        pyautogui.keyUp('ctrl')
                        cv2.putText(img, "ZOOMING IN +", (400, 90), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                    else:
                        cv2.putText(img, "(IDLE - Move Up/Down)", (400, 90), cv2.FONT_HERSHEY_PLAIN, 2, (150, 150, 150), 2)
                else:
                    zoom_anchor_y = 0

    # ------------------------------------------
    # GLOBAL TRACKING LOSS FAILSAFES
    # ------------------------------------------
    else:
        # Prevents ghost dragging if hands exit the frame mid-drag
        if is_dragging:
            pyautogui.mouseUp()
            is_dragging = False
            pinch_start_time = 0
            print("Failsafe Triggered: Mouse Released due to tracking loss.")
        
        # Reset all anchors and identity locks
        scroll_anchor_y = 0
        zoom_anchor_y = 0
        vol_anchor_x = 0
        primary_hand_label = None 

    # Render UI Window
    cv2.imshow("HAND POINTER-CONTROLLER", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Graceful Exit
cap.stop()
cv2.destroyAllWindows()