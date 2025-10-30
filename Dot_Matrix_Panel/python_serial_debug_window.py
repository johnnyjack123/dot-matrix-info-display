from flask import Flask, render_template_string
from flask_socketio import SocketIO
import threading
from Dot_Matrix_Panel.logger import logger

# Flask App für Serial Monitor
monitor_app = Flask(__name__)
monitor_app.config['SECRET_KEY'] = 'serial_monitor_secret'
socketio = SocketIO(monitor_app, cors_allowed_origins="*", async_mode='threading')

# HTML Template (bleibt gleich)
MONITOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ESP Serial Monitor</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #00ff00;
            margin: 0;
            padding: 20px;
        }
        h1 { color: #00ff00; }
        #output {
            height: 70vh;
            overflow-y: auto;
            border: 2px solid #00ff00;
            padding: 15px;
            background: #0a0a0a;
            border-radius: 5px;
        }
        .sent { color: #3498db; }
        .received { color: #2ecc71; }
        .error { color: #e74c3c; }
        .timestamp { color: #95a5a6; font-size: 0.8em; }
    </style>
</head>
<body>
    <h1>🔌 ESP Serial Monitor</h1>
    <div id="status">Connecting...</div>
    <div id="output"></div>

    <script>
        const socket = io();
        const output = document.getElementById('output');
        const status = document.getElementById('status');

        socket.on('connect', function() {
            status.innerHTML = '✓ Connected';
            status.style.color = '#2ecc71';
        });

        socket.on('disconnect', function() {
            status.innerHTML = '✗ Disconnected';
            status.style.color = '#e74c3c';
        });

        socket.on('serial_data', function(data) {
            const line = document.createElement('div');
            const time = new Date().toLocaleTimeString();

            if (data.type === 'sent') {
                line.className = 'sent';
                line.innerHTML = `<span class="timestamp">[${time}]</span> ← Python: ${data.message}`;
            } else if (data.type === 'received') {
                line.className = 'received';
                line.innerHTML = `<span class="timestamp">[${time}]</span> → ESP: ${data.message}`;
            } else if (data.type === 'error') {
                line.className = 'error';
                line.innerHTML = `<span class="timestamp">[${time}]</span> ✗ ${data.message}`;
            } else if (data.type === 'info') {
                line.style.color = '#f39c12';
                line.innerHTML = `<span class="timestamp">[${time}]</span> ℹ ${data.message}`;
            }

            output.appendChild(line);
            output.scrollTop = output.scrollHeight;
        });
    </script>
</body>
</html>
"""


@monitor_app.route('/')
def index():
    return render_template_string(MONITOR_HTML)


def send_messages(mode, msg):
    """
    Diese Funktion wird aus serial_connection.py aufgerufen.
    Sie sendet die Nachrichten per SocketIO an alle verbundenen Clients.
    """
    try:
        with monitor_app.app_context():
            socketio.emit('serial_data', {
                'type': mode,
                'message': msg
            }, namespace='/')
    except Exception as e:
        logger.error(f"SocketIO emit error: {e}")


@socketio.on('connect')
def handle_connect():
    """Wird aufgerufen wenn ein Client sich verbindet"""
    logger.info("Client mit Serial Monitor connected!")
    send_messages('info', 'Serial Monitor connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Wird aufgerufen wenn ein Client sich trennt"""
    logger.info("Client disconnected.")


def start_serial_monitor_server():
    """Startet den Serial Monitor Server auf Port 5001"""

    def run_server():
        logger.info("Serial monitor server starts on http://127.0.0.1:5001, because you are in debug mode.")
        socketio.run(monitor_app,
                     host='127.0.0.1',
                     port=5001,
                     debug=False,
                     allow_unsafe_werkzeug=True,
                     use_reloader=False)

    # Server in separatem Thread starten
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    logger.info("Started serial monitor server thread gestartet")
