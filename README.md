# AI Presenter Suite

## Overview

**AI Presenter Suite** is a multi-component system designed to facilitate smart, gesture-based control and management of presentations, screen recordings, and video sharing. It leverages computer vision, hand gesture recognition, networked device communication, and a web-based video platform for seamless classroom or remote presentation experiences.

---

## Features

- **Hand Gesture Control:** Use hand gestures to control slide navigation and start/stop screen recording.
- **Screen Recording:** Record your screen and audio, triggered by gestures.
- **Device Communication:** Connects Raspberry Pi and computers for remote control using Zeroconf/mDNS.
- **Web Video Platform:** Upload, browse, and stream recorded videos via a modern web interface.
- **YouTube Downloader:** Download YouTube videos for offline use.
- **Cross-Platform:** Components for Raspberry Pi, Windows, and web.

---

## Directory Structure

```
.
├── connectedsystem/      # Client for connecting to keyboard control server
├── detect/               # Hand gesture detection and screen recording
├── optimize/             # Optimized gesture and recording logic
├── sharescreen/          # Server/client for keyboard and screen sharing
├── testavi/              # Flask web app for video streaming (test)
├── web/                  # Main Flask web app for video management
├── scripts/              # Utility scripts
├── downvideoyoutube.py   # YouTube video downloader
├── README.md
```

---

## Installation

### System Requirements

- Python 3.7+
- pip
- (For Raspberry Pi) Raspbian OS

### Dependencies

Install system dependencies:

```bash
sudo apt update
sudo apt install libgtk2.0-dev pkg-config
```

Install Python dependencies:

```bash
pip install pynput flask flask-cors azure-storage-blob mediapipe opencv-python pyautogui zeroconf pytube pyaudio moviepy keyboard mss pillow pygame
```

---

## Components

### 1. Hand Gesture Detection & Screen Recording

- **Location:** `detect/`, `optimize/`
- **Description:** Uses OpenCV and MediaPipe to detect hand gestures via webcam. Gestures trigger slide navigation and screen recording.
- **Run:**
  ```bash
  python detect/testcampi.py
  # or
  python optimize/main.py
  ```

### 2. Device Communication

- **Location:** `connectedsystem/`, `sharescreen/`
- **Description:** Uses Zeroconf to discover and connect devices on the same network. Allows remote control of slides via gestures.
- **Run server (Raspberry Pi):**
  ```bash
  python sharescreen/keyboard_server.py
  ```
- **Run client (Computer):**
  ```bash
  python connectedsystem/computer_client.py
  ```

### 3. Web Video Platform

- **Location:** `web/`
- **Description:** Flask app for browsing, streaming, and downloading recorded videos. Integrates with Azure Blob Storage.
- **Run:**
  ```bash
  cd web
  python main.py
  ```
- **Access:** Open [http://localhost:5000](http://localhost:5000) in your browser.

### 4. YouTube Video Downloader

- **Location:** `downvideoyoutube.py`
- **Description:** Download YouTube videos for offline use.
- **Run:**
  ```bash
  python downvideoyoutube.py
  ```

---

## Usage

1. **Start the keyboard server on the Raspberry Pi.**
2. **Run the gesture detection script on your computer.**
3. **Use hand gestures to control slides and recording.**
4. **Recorded videos are uploaded to Azure Blob Storage.**
5. **Access the web platform to view, search, and download videos.**

---

## Configuration

- **Azure Blob Storage:** Update the connection string and container name in `web/main.py` and related files.
- **Network:** Ensure all devices are on the same local network for Zeroconf discovery.

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## Acknowledgements

- [MediaPipe](https://mediapipe.dev/)
- [OpenCV](https://opencv.org/)
- [Flask](https://flask.palletsprojects.com/)
- [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/)
- [Zeroconf](https://github.com/jstasiak/python-zeroconf)

---

## Technologies Used

- **Computer Vision & Hand Gesture Recognition:**
  - OpenCV (cv2) for image processing and camera capture.
  - MediaPipe for hand landmark detection and gesture recognition.

- **Screen Recording & Automation:**
  - PyAutoGUI for simulating keyboard inputs and screen capture.
  - MoviePy for video editing and merging audio/video streams.
  - PyAudio for audio recording.

- **Networking & Device Communication:**
  - Zeroconf (python-zeroconf) for automatic service discovery and device communication.
  - Socket programming for TCP/IP communication between devices.

- **Web Development:**
  - Flask for the backend web server.
  - Flask-CORS for handling Cross-Origin Resource Sharing.
  - HTML/CSS/JavaScript for the frontend interface.
  - Azure Blob Storage for storing and streaming video files.

- **Additional Libraries:**
  - PyTube for downloading YouTube videos.
  - NumPy for numerical operations.
  - Pillow (PIL) for image processing.
  - Pygame for audio playback (in some components).
  - MSS for screen capture (in the sharescreen component).

---

## Pushing to GitHub

To push this project to GitHub, follow these steps:

1. **Create a GitHub Repository:**
   - Go to [GitHub](https://github.com/) and sign in.
   - Click on the "+" icon in the top right corner and select "New repository."
   - Name your repository (e.g., `AI_presenter`).
   - Choose visibility (public or private).
   - Click "Create repository."

2. **Initialize Git in Your Project:**
   - Open a terminal in your project directory.
   - Run the following commands:
     ```bash
     git init
     git add .
     git commit -m "Initial commit"
     ```

3. **Link Your Local Repository to GitHub:**
   - Copy the URL of your GitHub repository (e.g., `https://github.com/yourusername/AI_presenter.git`).
   - Run the following command, replacing the URL with your repository URL:
     ```bash
     git remote add origin https://github.com/yourusername/AI_presenter.git
     ```

4. **Push Your Code to GitHub:**
   - Run the following command to push your code to the `main` branch:
     ```bash
     git push -u origin main
     ```

5. **Verify on GitHub:**
   - Go to your GitHub repository page to verify that your code has been pushed successfully.

---
