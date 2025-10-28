from flask_socketio import emit
import Dot_Matrix_Panel.global_variables as global_variables

socketio = None


def init_socket(socketio_instance):
    global socketio
    socketio = socketio_instance
    print("✓ SocketIO in sockets.py initialisiert")

    @socketio.on("connect")
    def handle_connect():
        print("✓ Client connected to main server")

    @socketio.on("request_status")
    def handle_request_status():
        print("Client fragt nach Status")
        emit('status_message', 'Server bereit')

    @socketio.on("request_esp_status")
    def handle_request_esp_status():
        """Client fragt nach ESP-Verbindungsstatus"""
        print("Client fragt nach ESP-Status")
        from Dot_Matrix_Panel.outsourced_functions import read

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
        print("⚠ Warnung: socketio noch nicht initialisiert!")
        return

    try:
        socketio.emit(name, msg)
        print(f"✓ Socket gesendet: {name} -> {msg}")
    except Exception as e:
        print(f"✗ Socket-Fehler: {e}")


def get_socketio():
    return socketio
