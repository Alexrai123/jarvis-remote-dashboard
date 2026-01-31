import os
import re
import webbrowser
import cv2
import platform
import pyautogui
import psutil
import time
from flask import Flask, request, jsonify, render_template_string, Response
from langchain_community.llms import Ollama
from AppOpener import open as app_open
import mss
import mss.tools
import numpy as np

app = Flask(__name__)
llm = Ollama(model="llama3")

# --- 1. CONFIGURARE ---
camera = cv2.VideoCapture(0)
camera_activa = True
screens_active = True

# --- 2. UNELTELE (TOOLS) ---

def tool_volume(args):
    try:
        clean_args = str(args).lower().replace('"', '').replace("'", "")
        
        # FIX: Acceptam si "minute" sau "minut" (confuzie frecventa cu mute)
        if "mute" in clean_args or "liniste" in clean_args or "minute" in clean_args or "minut" in clean_args:
            pyautogui.press("volumemute")
            return "Mute/Unmute executat."
            
        match = re.search(r"([+-]?\d+)", clean_args)
        if match:
            amount = int(match.group(1))
            presses = abs(amount) // 2
            if amount < 0:
                for _ in range(presses): pyautogui.press("volumedown")
                action = "scazut"
            else:
                for _ in range(presses): pyautogui.press("volumeup")
                action = "crescut"
            return f"Volum {action} cu {amount}%."
        return "Nu am inteles valoarea volumului."
    except Exception as e: return f"Eroare: {e}"

def tool_open_app(app_name):
    try:
        app_open(app_name, match_closest=True, output=False)
        return f"Deschid {app_name}."
    except: return f"Nu gasesc aplicatia {app_name}."

def tool_google(query):
    q = str(query).lower()
    
    # --- LOGICA SMART YOUTUBE ---
    if "youtube" in q:
        # Curatam cuvintele de legatura ca sa ramana doar ce cautam
        clean_q = q.replace("youtube", "").replace("cauta", "").replace("pe", "").replace("deschide", "").strip()
        
        # Deschidem direct cautarea pe YouTube
        webbrowser.open(f"https://www.youtube.com/results?search_query={clean_q}")
        return f"Deschid YouTube cu: {clean_q}"
        
    # --- LOGICA STANDARD GOOGLE ---
    else:
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Caut pe Google: {query}"

def tool_camera(action):
    global camera_activa
    if "stop" in str(action).lower() or "opre" in str(action).lower():
        camera_activa = False
        return "Camera oprita."
    else:
        camera_activa = True
        return "Camera pornita."

def tool_screens(action):
    global screens_active
    if "stop" in str(action).lower() or "opre" in str(action).lower() or "ascunde" in str(action).lower():
        screens_active = False
        return "Partajare ecrane oprita."
    else:
        screens_active = True
        return "Partajare ecrane pornita."

def tool_system(command):
    cmd = str(command).lower()
    
    # SIGURANTA: Nu opri muzica daca userul zice de ecrane
    if "ecran" in cmd or "monitor" in cmd or "video" in cmd:
        return "COMANDA RESPINSA: Ai incercat sa opresti muzica folosind comenzi video."

    if "lock" in cmd: 
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "PC Blocat."
    elif "shutdown" in cmd: 
        os.system("shutdown -s -t 60")
        return "Shutdown in 60s."
    elif "logout" in cmd or "delogare" in cmd or "iesi" in cmd:
        os.system("shutdown -l")
        return "La revedere! (Log Out)"
        
    # Media
    elif "pauza" in cmd or "play" in cmd: pyautogui.press("playpause")
    elif "stop" in cmd: pyautogui.press("stop")
    elif "next" in cmd: pyautogui.press("nexttrack")
    elif "back" in cmd: pyautogui.press("prevtrack")
        
    return "Comanda sistem executata."

def tool_chat(text): return text

# --- 3. CREIERUL ---

def decide_action(user_text):
    prompt = f"""
    Esti Jarvis. Raspunde STRICT in formatul: TOOL: nume || ARG: valoare
    
    REGULI:
    1. "Ecrane", "Monitor" -> TOOL: tool_screens || ARG: stop/start
    2. "Camera", "Webcam" -> TOOL: tool_camera || ARG: stop/start
    3. "Muzica", "Piesa", "Volum" -> TOOL: tool_system sau tool_volume.
    4. NU folosi tool_system pentru video!

    TOOLS:
    - tool_screens (ARG: stop, start)
    - tool_camera (ARG: stop, start)
    - tool_system (ARG: logout, lock, shutdown, play, pause, stop, next)
    - tool_volume (ARG: -20, +20, mute)
    - tool_open_app (ARG: nume)
    - tool_google (ARG: query)
    - tool_chat (ARG: raspuns)

    User: "{user_text}"
    Raspuns:
    """
    return llm.invoke(prompt).strip()

def execute_smart_command(ai_response):
    print(f"🤖 AI Raw: {ai_response}")
    tool_match = re.search(r"TOOL:\s*([a-zA-Z_0-9]+)", ai_response, re.IGNORECASE)
    arg_match = re.search(r"ARG:\s*(.*)", ai_response, re.IGNORECASE)

    if tool_match:
        tool_name = tool_match.group(1).lower().strip()
        argument = arg_match.group(1).strip() if arg_match else ""
        if "||" in argument: argument = argument.split("||")[0].strip()
        if "tool_" not in tool_name: tool_name = "tool_" + tool_name

        tools = {
            "tool_volume": tool_volume, "tool_open_app": tool_open_app,
            "tool_google": tool_google, "tool_system": tool_system,
            "tool_camera": tool_camera, "tool_chat": tool_chat,
            "tool_screens": tool_screens
        }
        
        if tool_name in tools: return tools[tool_name](argument)
            
    return ai_response

# --- 4. STREAMING ---

def gen_cam():
    global camera_activa
    while True:
        if camera_activa:
            success, frame = camera.read()
            if not success: frame = np.zeros((480, 640, 3), dtype=np.uint8)
            sleep_time = 0.05
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "CAMERA OFF", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
            sleep_time = 0.5
        try:
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        except: pass
        time.sleep(sleep_time)

def gen_monitor(mon_id):
    global screens_active
    with mss.mss() as sct:
        while True:
            try:
                if screens_active:
                    if mon_id >= len(sct.monitors): break
                    img = np.array(sct.grab(sct.monitors[mon_id]))
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    h, w, _ = img.shape
                    img = cv2.resize(img, (w//2, h//2))
                    sleep_time = 0.1
                else:
                    img = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(img, "SCREEN OFF", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                    sleep_time = 0.5
                ret, buffer = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                time.sleep(sleep_time)
            except: time.sleep(1)

# --- 5. RUTE ---

@app.route('/feed_cam')
def feed_cam(): return Response(gen_cam(), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/feed_mon/<int:mon_id>')
def feed_mon(mon_id): return Response(gen_monitor(mon_id), mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route('/get_monitors_count')
def get_monitors_count():
    with mss.mss() as sct: count = len(sct.monitors) - 1
    return jsonify({"count": count})
@app.route('/command', methods=['POST'])
def handle_command():
    data = request.json.get('command', '')
    return jsonify({"reply": execute_smart_command(decide_action(data))})
@app.route('/stats')
def stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return jsonify({"cpu": cpu, "ram": ram})

MOBILE_UI = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jarvis Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    body { background: #121212; color: #fff; font-family: sans-serif; text-align: center; margin:0; padding:5px; }
    .monitors { display: flex; flex-wrap: wrap; justify-content: center; gap: 5px; }
    .box { flex: 1 1 300px; border: 1px solid #333; border-radius: 8px; overflow: hidden; background: #000; position:relative; }
    .label { position:absolute; top:5px; left:5px; background:rgba(0,0,0,0.7); padding:2px 5px; color:#00d4ff; font-weight:bold; border-radius:4px; font-size:10px;}
    img { width: 100%; display: block; }
    
    /* Stiluri Grafic */
    .chart-container { width: 95%; margin: 10px auto; background: #1a1a1a; padding: 5px; border-radius: 10px; border: 1px solid #333; }
    
    .lang-box { margin: 10px 0; }
    .lang-btn { background: transparent; border: 1px solid #555; color: #888; padding: 5px 10px; border-radius: 15px; margin: 0 5px; cursor:pointer; font-weight:bold; font-size:12px;}
    .lang-btn.active { border-color: #00d4ff; color: #00d4ff; background: rgba(0, 212, 255, 0.1); }
    .mic { background: #ff4757; color: white; width: 60px; height: 60px; border-radius: 50%; border:none; font-size: 26px; margin: 10px; cursor: pointer; box-shadow: 0 0 10px rgba(255,71,87,0.3); }
    .send { background: #00d4ff; color: black; font-weight: bold; border:none; padding: 8px 15px; border-radius: 20px; cursor: pointer;}
    input { padding: 10px; width: 60%; border-radius: 20px; border: none; background: #222; color: #fff; outline:none; font-size:14px;}
    .listening { animation: pulse 1.5s infinite; background: #ff6b81; }
    @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); } 70% { box-shadow: 0 0 0 20px rgba(0, 0, 0, 0); } }
</style>
</head>
<body onload="init()">
    <h3>JARVIS DASHBOARD</h3>
    
    <div class="monitors" id="screen_area">
        <div class="box"><div class="label">WEBCAM</div><img src="/feed_cam"></div>
    </div>
    
    <div class="chart-container">
        <canvas id="resChart" height="80"></canvas>
    </div>

    <div class="lang-box">
        <button id="ro" class="lang-btn active" onclick="setL('ro-RO')">RO 🇷🇴</button>
        <button id="en" class="lang-btn" onclick="setL('en-US')">EN 🇺🇸</button>
    </div>

    <button class="mic" id="mic" onclick="start()">🎤</button>
    <br>
    <div style="display:flex; justify-content:center; gap:5px;">
        <input id="inp" placeholder="Zi comanda...">
        <button class="send" onclick="snd()">🚀</button>
    </div>
    <div id="stat" style="color:#888; margin-top:10px; font-size:12px;">Ready.</div>

    <script>
        // --- LOGICA GRAFIC (Chart.js) ---
        var ctx = document.getElementById('resChart').getContext('2d');
        var resChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['CPU', 'RAM'],
                datasets: [{
                    label: '%',
                    data: [0, 0],
                    backgroundColor: ['rgba(255, 71, 87, 0.8)', 'rgba(0, 212, 255, 0.8)'],
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', // Bare orizontale
                responsive: true,
                scales: { x: { min: 0, max: 100, grid: {color: '#333'} }, y: { grid: {display: false}, ticks: {color: '#fff'} } },
                plugins: { legend: {display: false} }
            }
        });

        // Actualizam la fiecare 1.5 secunde
        setInterval(async () => {
            try {
                let r = await fetch('/stats');
                let d = await r.json();
                resChart.data.datasets[0].data = [d.cpu, d.ram];
                resChart.update();
            } catch(e) {}
        }, 1500);

        // --- RESTUL SCRIPTURILOR ---
        var lang = 'ro-RO';
        function setL(l) { 
            lang=l; 
            document.getElementById('ro').className = l=='ro-RO' ? 'lang-btn active' : 'lang-btn';
            document.getElementById('en').className = l=='en-US' ? 'lang-btn active' : 'lang-btn';
        }
        async function init() {
            try {
                var r = await fetch('/get_monitors_count');
                var d = await r.json();
                for(let i=1; i<=d.count; i++) {
                    var div = document.createElement('div'); div.className='box';
                    div.innerHTML = `<div class="label">MONITOR ${i}</div><img src="/feed_mon/${i}">`;
                    document.getElementById('screen_area').appendChild(div);
                }
            } catch(e) {}
        }
        function start() {
            if (!window.webkitSpeechRecognition) { alert("Foloseste Chrome!"); return; }
            var r = new webkitSpeechRecognition(); r.lang = lang; 
            document.getElementById('mic').classList.add('listening');
            r.onresult = function(e) { 
                document.getElementById('inp').value = e.results[0][0].transcript;
                document.getElementById('mic').classList.remove('listening');
                snd();
            };
            r.onerror = function() { document.getElementById('mic').classList.remove('listening'); };
            r.start();
        }
        async function snd() {
            var t = document.getElementById('inp').value; if(!t) return;
            document.getElementById('stat').innerText = "Procesez...";
            try {
                var r = await fetch('/command', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({command:t})});
                var d = await r.json();
                document.getElementById('stat').innerText = d.reply;
                document.getElementById('inp').value = "";
            } catch(e) { document.getElementById('stat').innerText = "Eroare."; }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(MOBILE_UI)
if __name__ == '__main__': app.run(host='0.0.0.0', port=5000, threaded=True)