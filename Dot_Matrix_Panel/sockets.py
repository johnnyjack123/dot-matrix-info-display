from flask_socketio import emit

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
        # Sende Status an den anfragenden Client
        emit('status_message', 'Loading...')


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
