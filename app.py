from flask import Flask, render_template_string, request, jsonify, send_from_directory
import requests
import os

import json
from flask import Flask, render_template_string, request, jsonify, Response
import requests

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AV Buddy</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #111; color: #fff; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #222; padding: 15px; text-align: center; font-size: 22px; font-weight: bold; border-bottom: 2px solid #333; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .logo-icon { font-size: 28px; }
        .chat-box { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 12px 16px; border-radius: 20px; max-width: 80%; word-wrap: break-word; font-size: 16px; line-height: 1.4; }
        .user { background: #007bff; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai { background: #333; align-self: flex-start; border-bottom-left-radius: 2px; }
        .input-area { display: flex; padding: 12px; background: #222; gap: 10px; border-top: 1px solid #333; }
        input { flex: 1; padding: 14px; border: none; border-radius: 25px; background: #444; color: #fff; font-size: 16px; outline: none; }
        button { background: #28a745; border: none; color: white; padding: 0 22px; border-radius: 25px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); display:flex; align-items:center; justify-content:center; z-index:1000; }
        .modal-content { background:#222; padding:30px; border-radius:20px; text-align:center; border:1px solid #444; width:80%; max-width:350px; }
        .modal-content h3 { margin-top:0; }
        .modal-content input { width:90%; margin-bottom:15px; display:block; margin-left:auto; margin-right:auto; }
    </style>
</head>
<body>

    <div class="modal" id="nameModal">
        <div class="modal-content">
            <h3>🤖 Welcome to AV</h3>
            <p>Please enter your name:</p>
            <input type="text" id="usernameInput" placeholder="Your Name...">
            <button onclick="saveName()">Enter</button>
        </div>
    </div>

    <div class="header">
        <span class="logo-icon">📦🤖</span> 
        <span id="appHeader">AV Robot Buddy</span>
    </div>
    
    <div class="chat-box" id="chat">
        <div class="msg ai" id="welcomeMessage">Hello! I am AV, your cardboard robot buddy. How can I help you today?</div>
    </div>
    <div class="input-area">
        <input type="text" id="msgInput" placeholder="Type a message..." onkeypress="if(event.key==='Enter')send()">
        <button onclick="send()">Send</button>
    </div>

    <script>
        let currentUserName = "User";

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }

        window.onload = function() {
            let saved = localStorage.getItem("av_user_name");
            if(saved) {
                currentUserName = saved;
                document.getElementById("nameModal").style.display = "none";
                applyUserIdentity();
            }
        }

        function saveName() {
            let nameInput = document.getElementById("usernameInput").value.trim();
            if(!nameInput) nameInput = "Azan";
            currentUserName = nameInput;
            localStorage.setItem("av_user_name", nameInput);
            document.getElementById("nameModal").style.display = "none";
            applyUserIdentity();
        }

        function applyUserIdentity() {
            document.getElementById("appHeader").innerText = "Hello " + currentUserName + " | AV";
            document.getElementById("welcomeMessage").innerText = "Hello " + currentUserName + "! I am AV, your cardboard robot buddy. How can I help you today? / السلام علیکم " + currentUserName + "! میں اے وی ہوں۔ میں آپ کی کیا مدد کر سکتا ہوں؟";
        }

        async function send() {
            let input = document.getElementById("msgInput");
            let text = input.value.trim();
            if (!text) return;
            
            appendMessage(text, 'user');
            input.value = "";

            try {
                let response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text, username: currentUserName})
                });
                let data = await response.json();
                appendMessage(data.reply, 'ai');
            } catch (e) {
                appendMessage("Error communicating with server.", 'ai');
            }
        }

        function appendMessage(text, sender) {
            let chat = document.getElementById("chat");
            let msg = document.createElement("div");
            msg.className = "msg " + sender;
            msg.innerText = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/manifest.json')
def manifest():
    data = {
        "short_name": "AV Buddy",
        "name": "AV Cardboard Robot Buddy",
        "icons": [
            {
                "src": "https://flaticon.com",
                "type": "image/png",
                "sizes": "512x512"
            }
        ],
        "start_url": "/",
        "background_color": "#111111",
        "theme_color": "#222222",
        "display": "standalone",
        "orientation": "portrait"
    }
    return Response(json.dumps(data), mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    sw_code = """
    self.addEventListener('install', function(e) {
        self.skipWaiting();
    });
    self.addEventListener('fetch', function(e) {
        e.respondWith(fetch(e.request));
    });
    """
    return Response(sw_code, mimetype='application/javascript')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message')
    username = data.get('username', 'User')
    full_prompt = f"The user's name is {username}. Remember to address them as {username} if natural. User message: {user_msg}"
    
    try:
        r = requests.post('http://localhost:11434/api/generate', 
                          json={"model": "av", "prompt": full_prompt, "stream": False},
                          timeout=30)
        ai_reply = r.json().get('response', 'Error connecting to AV.')
    except Exception:
        ai_reply = "AV is online! Please ensure 'ollama serve' is running in another Termux session."
    return jsonify({"reply": ai_reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AV</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#222222">
    
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #111; color: #fff; display: flex; flex-direction: column; height: 100vh; }
        .header { background: #222; padding: 15px; text-align: center; font-size: 22px; font-weight: bold; border-bottom: 2px solid #333; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .logo-emoji { font-size: 28px; }
        .chat-box { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 12px 16px; border-radius: 20px; max-width: 80%; word-wrap: break-word; font-size: 16px; line-height: 1.4; }
        .user { background: #007bff; align-self: flex-end; border-bottom-right-radius: 2px; }
        .ai { background: #333; align-self: flex-start; border-bottom-left-radius: 2px; }
        .input-area { display: flex; padding: 12px; background: #222; gap: 10px; border-top: 1px solid #333; }
        input { flex: 1; padding: 14px; border: none; border-radius: 25px; background: #444; color: #fff; font-size: 16px; outline: none; }
        button { background: #28a745; border: none; color: white; padding: 0 22px; border-radius: 25px; font-size: 16px; font-weight: bold; cursor: pointer; }
        
        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); display:flex; align-items:center; justify-content:center; z-index:1000; }
        .modal-content { background:#222; padding:30px; border-radius:20px; text-align:center; border:1px solid #444; width:80%; max-width:350px; }
        .modal-content h3 { margin-top:0; }
        .modal-content input { width:90%; margin-bottom:15px; display:block; margin-left:auto; margin-right:auto; }
    </style>
</head>
<body>

    <div class="modal" id="nameModal">
        <div class="modal-content">
            <div class="logo-emoji" style="font-size: 60px; margin-bottom: 10px;">🤖</div>
            <h3>🤖 Welcome to AV</h3>
            <p>Please enter your name:</p>
            <input type="text" id="usernameInput" placeholder="Your Name...">
            <button onclick="saveName()">Enter</button>
        </div>
    </div>

    <div class="header">
        <span class="logo-emoji">🤖</span>
        <span id="appHeader">AV Robot Buddy</span>
    </div>
    
    <div class="chat-box" id="chat">
        <div class="msg ai" id="welcomeMessage">Hello! I am AV, your cardboard robot buddy. How can I help you today?</div>
    </div>
    <div class="input-area">
        <input type="text" id="msgInput" placeholder="Type a message..." onkeypress="if(event.key==='Enter')send()">
        <button onclick="send()">Send</button>
    </div>

    <script>
        let currentUserName = "User";

        window.onload = function() {
            let saved = localStorage.getItem("av_user_name");
            if(saved) {
                currentUserName = saved;
                document.getElementById("nameModal").style.display = "none";
                applyUserIdentity();
            }
        }

        function saveName() {
            let nameInput = document.getElementById("usernameInput").value.trim();
            if(!nameInput) nameInput = "Azaan";
            currentUserName = nameInput;
            localStorage.setItem("av_user_name", nameInput);
            document.getElementById("nameModal").style.display = "none";
            applyUserIdentity();
        }

        function applyUserIdentity() {
            document.getElementById("appHeader").innerText = "Hello " + currentUserName + " | AV";
            document.getElementById("welcomeMessage").innerText = "Hello " + currentUserName + "! I am AV, your cardboard robot buddy. How can I help you today? / السلام علیکم " + currentUserName + "! میں اے وی ہوں۔ میں آپ کی کیا مدد کر سکتا ہوں؟";
        }

        async function send() {
            let input = document.getElementById("msgInput");
            let text = input.value.trim();
            if (!text) return;
            
            appendMessage(text, 'user');
            input.value = "";

            try {
                let response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text, username: currentUserName})
                });
                let data = await response.json();
                appendMessage(data.reply, 'ai');
            } catch (e) {
                appendMessage("Error communicating with server.", 'ai');
            }
        }

        function appendMessage(text, sender) {
            let chat = document.getElementById("chat");
            let msg = document.createElement("div");
            msg.className = "msg " + sender;
            msg.innerText = text;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_msg = data.get('message')
    username = data.get('username', 'User')
    full_prompt = f"The user's name is {username}. Remember to address them as {username} if natural. User message: {user_msg}"
    
    try:
        r = requests.post('http://localhost:11434/api/generate', 
                          json={"model": "av", "prompt": full_prompt, "stream": False},
                          timeout=30)
        ai_reply = r.json().get('response', 'Error connecting to AV.')
    except Exception:
        ai_reply = "AV is online! Please ensure 'ollama serve' is running in another Termux session."
    return jsonify({"reply": ai_reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
