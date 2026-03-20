import os
import time
import requests
import logging
from flask import Flask, jsonify, render_template_string

# --- SETUP LOGGING ---
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- STORAGE DATA (Global State) ---
# Kita simpan dalam dictionary supaya data konsisten dalam session Flask
state = {
    "history": [],
    "last_issue": None,
    "win": 0,
    "lose": 0,
    "streak": 0
}

def get_bs(n):
    """Tukar nombor kepada BIG atau SMALL"""
    return "BIG" if int(n) >= 5 else "SMALL"

def get_prediction(data_list):
    """Logik AI V5 Shadow - Analisis Pola"""
    if len(data_list) < 5:
        return "BIG", "SCANNING"
    
    # Ambil saiz dari 2 data terakhir
    r1 = get_bs(data_list[0]["number"])
    r2 = get_bs(data_list[1]["number"])
    
    # Pola Mudah: Jika sama, ikut (Follow). Jika beza, tukar (P-Pong).
    if r1 == r2:
        return r1, "FOLLOW"
    else:
        return ("SMALL" if r1 == "BIG" else "BIG"), "P-PONG"

@app.route('/api/data')
def api_data():
    global state
    try:
        # Request data dari server WinGo
        ts = int(time.time() * 1000)
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36",
            "Accept": "application/json"
        }
        url = f"https://draw.ar-lottery01.com/WinGo/WinGo_1M/GetHistoryIssuePage.json?ts={ts}"
        
        r = requests.get(url, headers=headers, timeout=10)
        res = r.json()
        
        if "data" not in res or "list" not in res["data"]:
            return jsonify({"status": "error", "message": "API WinGo Offline"})

        all_list = res["data"]["list"]
        latest_now = all_list[0]
        issue_now = str(latest_now["issue"])
        num_now = int(latest_now["number"])
        size_now = get_bs(num_now)

        # Jika ada period/issue baru dikesan
        if issue_now != state["last_issue"]:
            # 1. Update result ramalan yang lepas
            for item in state["history"]:
                if item["issue"] == issue_now and item["status"] == "WAIT":
                    item["result"] = f"{size_now} ({num_now})"
                    if item["pred"] == size_now:
                        state["win"] += 1
                        state["streak"] = (state["streak"] + 1) if state["streak"] >= 0 else 1
                        item["status"] = "WIN"
                    else:
                        state["lose"] += 1
                        state["streak"] = (state["streak"] - 1) if state["streak"] <= 0 else -1
                        item["status"] = "LOSE"

            # 2. Buat ramalan baru untuk issue akan datang (Issue + 1)
            next_issue = str(int(issue_now) + 1)
            pred, ai_type = get_prediction(all_list)
            
            new_entry = {
                "issue": next_issue,
                "pred": pred,
                "ai": ai_type,
                "result": "Menunggu...",
                "status": "WAIT"
            }
            
            state["history"].insert(0, new_entry)
            
            # Hadkan history kepada 10 baris sahaja
            if len(state["history"]) > 10:
                state["history"].pop()
                
            state["last_issue"] = issue_now

        return jsonify({
            "status": "success",
            "history": state["history"],
            "win": state["win"],
            "lose": state["lose"],
            "streak": state["streak"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- UI FRONTEND (CYBERPUNK STYLE) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="ms">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MySGAME AI PRO V5.2</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Share Tech Mono', monospace; background: #050505; color: #00ffcc; text-align: center; min-height: 100vh; padding: 20px; }
        .container { max-width: 500px; margin: auto; border: 1px solid #00ffcc; padding: 15px; border-radius: 10px; background: rgba(0, 255, 204, 0.05); box-shadow: 0 0 15px rgba(0, 255, 204, 0.2); }
        h2 { color: #ffeb3b; text-shadow: 0 0 5px #ffeb3b; margin-bottom: 10px; }
        .stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
        .stat-card { border: 1px solid #444; padding: 10px; background: #000; border-radius: 5px; }
        .stat-card span { font-size: 0.8rem; color: #888; display: block; }
        .stat-card strong { font-size: 1.2rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.85rem; }
        th { background: #0a1919; color: #ffcc00; padding: 8px; border: 1px solid #00ffcc; }
        td { padding: 10px 5px; border: 1px solid #222; }
        .win-badge { color: #00ff00; font-weight: bold; }
        .lose-badge { color: #ff3333; font-weight: bold; }
        .wait-badge { color: #ffcc00; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.3; } }
        input { width: 100%; padding: 12px; margin: 10px 0; background: #111; border: 1px solid #00ffcc; color: #fff; text-align: center; font-family: inherit; }
        button { width: 100%; padding: 12px; background: #00ffcc; color: #000; border: none; font-weight: bold; cursor: pointer; border-radius: 5px; }
    </style>
</head>
<body>
    <div id="login-screen" class="container">
        <h2>TERMINAL MySGAME</h2>
        <p style="font-size: 0.8rem; color: #888;">Sila masukkan ID Akses untuk sambungan server.</p>
        <input type="password" id="access-id" placeholder="ID AKSES">
        <button onclick="doLogin()">SAMBUNG SISTEM</button>
    </div>

    <div id="main-screen" class="container" style="display:none;">
        <h2>V5.2 AI PREDICTOR</h2>
        <div class="stats">
            <div class="stat-card"><span>TOTAL WIN</span><strong id="w-val" style="color:#0f0;">0</strong></div>
            <div class="stat-card"><span>TOTAL LOSE</span><strong id="l-val" style="color:#f00;">0</strong></div>
            <div class="stat-card"><span>STREAK</span><strong id="s-val">0</strong></div>
            <div class="stat-card"><span>STATUS</span><strong style="color:#00ffcc; font-size:0.7rem;">CONNECTED</strong></div>
        </div>
        <table>
            <thead>
                <tr><th>Period</th><th>Predik</th><th>Result</th><th>Status</th></tr>
            </thead>
            <tbody id="table-body"></tbody>
        </table>
        <p id="msg" style="margin-top:10px; font-size:0.7rem; color:#555;">Menunggu data baru dari server...</p>
    </div>

    <script>
        const KEY = "Wan00"; 

        function doLogin() {
            const input = document.getElementById('access-id').value;
            if(input === KEY) {
                document.getElementById('login-screen').style.display = 'none';
                document.getElementById('main-screen').style.display = 'block';
                startSync();
            } else { alert("ID Akses Salah!"); }
        }

        async function updateUI() {
            try {
                const r = await fetch('/api/data');
                const d = await r.json();
                if(d.status === "success") {
                    document.getElementById('w-val').innerText = d.win;
                    document.getElementById('l-val').innerText = d.lose;
                    document.getElementById('s-val').innerText = (d.streak > 0 ? "+" : "") + d.streak;
                    
                    let rows = "";
                    d.history.forEach(item => {
                        let sClass = item.status === "WIN" ? "win-badge" : (item.status === "LOSE" ? "lose-badge" : "wait-badge");
                        rows += `<tr>
                            <td>${item.issue.slice(-4)}</td>
                            <td style="color:#ffcc00; font-weight:bold;">${item.pred}</td>
                            <td>${item.result}</td>
                            <td><span class="${sClass}">${item.status}</span></td>
                        </tr>`;
                    });
                    document.getElementById('table-body').innerHTML = rows;
                    document.getElementById('msg').innerText = "Update Terakhir: " + new Date().toLocaleTimeString();
                }
            } catch(e) { console.log("Sync Error"); }
        }

        function startSync() {
            updateUI();
            setInterval(updateUI, 4000); // Sync setiap 4 saat
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CODE)

if __name__ == '__main__':
    # PORT environment variable wajib untuk Render.com
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
