from flask_socketio import emit
import global_variables as global_variables
from logger import logger

socketio = None

def init_socket(socketio_instance):
    global socketio
    socketio = socketio_instance
    print("SocketIO in sockets.py initialisiert")

    @socketio.on("connect")
    def handle_connect():
        logger.info("Client connected to main server")

    @socketio.on("request_status")
    def handle_request_status():
        emit('status_message', 'Server bereit')

    @socketio.on("request_esp_status")
    def handle_request_esp_status():
        """Client fragt nach ESP-Verbindungsstatus"""

        connected = global_variables.connected
        emit('esp_connection_status', {'connected': connected})

    @socketio.on("request_esp_serial_status")
    def handle_request_esp_status():
        if global_variables.handshake:
            msg = "connected"
        else:
            msg = "disconnected"
        emit('status_message_serial', msg)

def send_socket(name, msg):
    if socketio is None:
        logger.warning("Socketio not initialized.")
        return

    try:
        socketio.emit(name, msg)
    except Exception as e:
        logger.error(f"Socket-Error: {e}")

def get_socketio():
    return socketio
