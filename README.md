# 🖐️ Hand Pointer-Controller

A real-time, zero-latency computer vision interface that turns your standard webcam into a spatial mouse.

Built with Python, OpenCV, and MediaPipe, this controller completely replaces a physical mouse, translating real-time hand gestures into cursor movements, clicks, scrolling, and system volume control. It utilizes a custom background threading architecture for the webcam feed and implements an adaptive One Euro Filter to dynamically eliminate cursor jitter and lag.

## ✨ Key Features

* **Zero Hardware Latency:** Asynchronous video capturing in a background thread bypasses camera I/O bottlenecks.
* **Dynamic Smoothing:** Integrates a One Euro Filter for adaptive high-speed tracking and low-speed stability (eliminates jitter).
* **Ambidextrous Identity Lock:** The system automatically assigns primary mouse controls to the first hand that enters the frame and locks it, preventing accidental hand-swapping.
* **Bimanual Interaction:** Bring a second hand into the frame to unlock modifier actions (like zooming) without disrupting your primary pointer.
* **Taskbar Reach:** Asymmetrical ROI padding ensures you can reach the edges of your monitor without your hand falling out of the camera's tracking boundary.

## 🚀 Quick Start (For Non-Developers)

If you just want to use the controller without installing Python:

1. Go to the **Releases** tab on the right side of this repository.
2. Download the latest `hand_pointer_controller.exe`.
3. Double-click the file to run it. *(Note: It may take 3-5 seconds to extract its AI models before your webcam light turns on).*

## 💻 Developer Setup

If you want to run the raw Python script or modify the code, it is highly recommended to use a Virtual Environment to avoid dependency conflicts.

### 1. Clone the repository

```bash
git clone [https://github.com/YOUR_USERNAME/hand-pointer-controller.git](https://github.com/YOUR_USERNAME/hand-pointer-controller.git)
cd hand-pointer-controller
```

### 2. Create and activate a Virtual Environment

**On Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

**On Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

*(If you don't have a requirements.txt, manually install: `pip install opencv-python mediapipe pyautogui numpy`)*

### 4. Run the Controller

```bash
python hand_pointer_controller.py
```

## 🎮 Gesture Controls

### Primary Hand (Mouse Control)

* **Move Cursor:** Raise Index Finger only.
* **Left Click:** Open Hand (all 4 fingers up) -> Quick Pinch (Thumb to Index).
* **Grab & Drag:** Open Hand -> Hold Pinch for 1.3 seconds until the loading ring completes.
* **Right Click:** Raise Index, Middle, and Ring fingers -> Quick Pinch (Thumb to Ring).
* **Double Click:** Raise Index and Pinky fingers -> Quick Pinch (Thumb to Index).
* **Scroll Page:** Raise Index and Middle (Peace Sign) -> Move hand up or down past the invisible deadzone.
* **Volume Control:** Raise Pinky (Shaka sign) -> Move hand left or right.
* **Pause/Clutch:** Closed Fist.

### Secondary Hand (Modifiers)

* **Zoom In/Out:** Raise Index and Middle (Peace Sign) -> Move hand down to zoom in, up to zoom out.

## 🛠️ Building the .exe Yourself

If you make changes to the code and want to compile your own executable, use PyInstaller. Because MediaPipe uses hidden C++ binaries, you must use the `--collect-all` flag to prevent crashing.

```bash
python -m pip install pyinstaller
.\venv\Scripts\pyinstaller.exe --onefile --noconsole --collect-all pyautogui --add-data "PATH\TO\YOUR\venv\Lib\site-packages\mediapipe\modules;mediapipe/modules" hand_pointer_controller.py
```
