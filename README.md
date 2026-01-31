# Jarvis Remote Dashboard

A powerful, customizable remote control dashboard for your Windows PC, powered by a local LLM (Llama 3 via Ollama) and Python.

## Features

*   **Smart Voice/Text Commands**: Control your PC using natural language (e.g., "Mute volume", "Open Spotify", "Lock PC"). Powered by Ollama.
*   **Live Dashboard**: Mobile-friendly web interface to see your PC's status.
*   **Video Streaming**:
    *   **Webcam Feed**: View your PC's webcam remotely.
    *   **Screen Share**: View your active monitors in real-time.
*   **System Control**:
    *   Volume Control (Up, Down, Mute)
    *   Media (Play/Pause, Next/Prev)
    *   Power (Shutdown, Lock, Logout)
    *   App Launcher
*   **Monitoring**: Real-time CPU and RAM usage charts.

## Prerequisites

*   **Python 3.8+**
*   **Ollama**: Installed and running with the `llama3` model pulled (`ollama pull llama3`).
*   **Windows**: Designed primarily for Windows (due to `pyautogui`, `cv2`, `mss` usage patterns).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/Alexrai123/jarvis-remote-dashboard.git
    cd jarvis-remote-dashboard
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Ensure **Ollama** is running locally.
2.  Start the server:
    ```bash
    python remote_server.py
    ```
3.  Access the dashboard in your browser:
    *   Local: `http://localhost:5000`
    *   Network: `http://<YOUR_PC_IP>:5000`

## Security Warning

⚠️ **Use with Caution**: This application allows **full remote control** of your PC (shell commands, screen capture, camera). It currently **does not** have built-in authentication.
*   Do not expose this port to the public internet without a secure tunnel (like Cloudflare Zero Trust) with authentication middleware.
*   Only use on trusted private networks.

## Technologies

*   **Backend**: Flask (Python)
*   **LLM Interface**: LangChain Community + Ollama
*   **Computer Vision**: OpenCV, MSS
*   **Automation**: PyAutoGUI, AppOpener
