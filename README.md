# **🖐️ Spatial Camera Pointer Controller**

A real-time, bimanual computer vision interface that turns your standard webcam into a spatial mouse.

Built with Python, OpenCV, and MediaPipe, this controller allows you to navigate your operating system, click, drag, scroll, and zoom using natural hand gestures. It features an ambidextrous "first-hand-priority" system and utilizes a secondary hand for modifier actions like zooming.

## **✨ Key Features**

* **Ambidextrous Primary Control:** The system automatically assigns primary mouse controls to the first hand that enters the camera frame.  
* **Bimanual Interaction:** Bring a second hand into the frame to unlock modifier actions (like zooming) without disrupting your primary pointer.  
* **Joystick-Style Scrolling & Zooming:** Instead of 1-to-1 trackpad scrolling which causes jitter, this uses a threshold-based "joystick" mechanism for perfectly smooth, continuous scrolling and zooming.  
* **Hardware Agnostic:** Runs entirely on standard RGB webcams (no depth sensors or IR tracking required).

## **🚀 Quick Start (For Non-Developers)**

If you just want to use the controller without installing Python:

1. Go to the [**Releases**](http://docs.google.com/releases) tab on the right side of this repository.  
2. Download the latest camera\_pointer\_controller.exe.  
3. Double-click the file to run it. *(Note: It may take 3-5 seconds to extract its AI models before your webcam light turns on).*

## **💻 Developer Setup**

If you want to run the raw Python script or modify the code, it is highly recommended to use a Virtual Environment to avoid dependency conflicts.

### **1\. Clone the repository**
```bash
git clone \[https://github.com/YOUR\_USERNAME/camera-pointer-controller.git\](https://github.com/YOUR\_USERNAME/camera-pointer-controller.git)  
cd camera-pointer-controller
```
### **2\. Create and activate a Virtual Environment**

**On Windows:**
```bahh
python \-m venv venv  
.\\venv\\Scripts\\activate
```
**On Linux/Mac:**
```bash
python3 \-m venv venv  
source venv/bin/activate
```
### **3\. Install Dependencies**
```bash
pip install \-r requirements.txt
```
### **4\. Run the Controller**
```bash
python camera\_pointer\_controller.py
```
## **🎮 Gesture Controls**

### **Primary Hand (Mouse Control)**

* **Move Cursor:** Raise Index Finger only.  
* **Left Click:** Open Hand (all 4 fingers up) \-\> Quick Pinch (Thumb to Index).  
* **Grab & Drag:** Open Hand \-\> Hold Pinch for 1.3 seconds until the loading ring completes.  
* **Right Click:** Raise Index, Middle, and Ring fingers \-\> Quick Pinch (Thumb to Ring).  
* **Double Click:** Raise Index and Pinky fingers \-\> Quick Pinch (Thumb to Index).  
* **Scroll Page:** Raise Index and Middle (Peace Sign) \-\> Move hand up or down past the invisible deadzone.  
* **Volume Control:** Raise Pinky (Shaka sign) \-\> Move hand left or right.  
* **Pause/Clutch:** Closed Fist.

### **Secondary Hand (Modifiers)**

* **Zoom In/Out:** Raise Index and Middle (Peace Sign) \-\> Move hand down to zoom in, up to zoom out.

## **🛠️ Building the .exe Yourself**

If you make changes to the code and want to compile your own executable, use PyInstaller. Because MediaPipe uses hidden C++ binaries, you must use the \--collect-all flag to prevent crashing.
```bash
python \-m pip install pyinstaller  
.\\venv\\Scripts\\pyinstaller.exe \--onefile \--noconsole \--collect-all pyautogui \--add-data "PATH\\TO\\YOUR\\venv\\Lib\\site-packages\\mediapipe\\modules;mediapipe/modules" camera\_pointer\_controller.py  
```
