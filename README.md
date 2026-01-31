# 🧠 Jarvis - Autonomous Local AI Agent

A multimodal, privacy-first AI agent designed to run locally on Windows. It perceives its environment through computer vision, listens via voice input, and executes system-level actions autonomously using **Function Calling**.

## 🚀 Key Features

* **🤖 Local LLM Orchestration:** Powered by **Llama 3** (via Ollama) & **LangChain**.
* **🛠️ Agentic Capabilities:** The AI autonomously decides when to trigger tools (Lock PC, Open Apps, Search Web) based on intent.
* **⚡ Low-Latency Architecture:** Uses Python `threading` and `queues` to decouple Model Inference, TTS, and Video Streaming for real-time performance.
* **👁️ Computer Vision:** Live streaming of Webcam & Desktop via **OpenCV** & **MSS** to a mobile-responsive dashboard.
* **🔐 Secure Remote Access:** Production-ready exposure via **Nginx Reverse Proxy** and **Cloudflare Tunnels**.
* **📊 Monitoring:** Real-time CPU/RAM visualization.

## 📱 Dashboard
*(Add a screenshot of your phone screen here)*

## 🛠️ Tech Stack
* **Core:** Python 3.x, Flask (Async)
* **AI:** Ollama, LangChain
* **Vision:** OpenCV, MSS
* **Automation:** PyAutoGUI, AppOpener
* **Infrastructure:** Nginx, Cloudflare Zero Trust

## ⚙️ Installation

1.  **Prerequisites:**
    * Python 3.10+
    * Ollama with `llama3` model pulled.
    * Nginx & Cloudflare (optional for remote access).

2.  **Setup:**
    ```bash
    git clone [https://github.com/Alexrai123/jarvis-remote-dashboard.git](https://github.com/Alexrai123/jarvis-remote-dashboard.git)
    cd jarvis-remote-dashboard
    pip install -r requirements.txt
    ```

3.  **Running:**
    * Double click the included `START_JARVIS.bat` to launch Ollama, Nginx, Cloudflare, and the Python Brain simultaneously.
    * *Or manually:* `python jarvis.py`

## ⚠️ Security
Allows full remote control. Use only behind secure tunnels (Cloudflare) or VPNs.

```mermaid
graph TD
    User[📱 Mobile User] -->|HTTPS| CF[Cloudflare Tunnel]
    CF -->|Reverse Proxy| Nginx[Nginx Server]
    Nginx -->|Request| Flask[Flask Backend]
    
    subgraph "Jarvis Core (Local PC)"
        Flask -->|Video Feed| CV[OpenCV/MSS]
        Flask -->|Text Prompt| LLM[Ollama / Llama3]
        LLM -->|Decision| Tools[Tool Execution]
        Tools -->|Action| Sys[Windows System / Apps]
        Tools -->|Reply| TTS[Voice Engine (Threaded)]
    end
```
