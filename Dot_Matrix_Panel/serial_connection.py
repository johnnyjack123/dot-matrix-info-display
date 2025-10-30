import serial
from serial.tools import list_ports
import time
import threading

from Dot_Matrix_Panel.outsourced_functions import read, save
from Dot_Matrix_Panel.python_serial_debug_window import send_messages
import Dot_Matrix_Panel.global_variables as global_variables
from Dot_Matrix_Panel.logger import logger

ser = None


def connect(esp_port):
    global ser
    baud_rate = 9600
    ser = serial.Serial(esp_port.device, baud_rate, timeout=5)
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    logger.info(f"Connected with ESP on port {esp_port.device}.")
    return


def get_port():
    while True:
        if not global_variables.connected:
            file = read()
            esp_data = file["esp_data"]
            if esp_data["ssid"] and esp_data["password"]:
                while not global_variables.connected:
                    ports = list_ports.comports()
                    if not ports:
                        logger.error("No esp on serial found.")
                        return "No ESP found"
                    for x, esp_port in enumerate(ports):
                        try:
                            logger.info(f"ESP port interface: {esp_port.device}")
                            connect(esp_port)
                            wait_until = time.time() + 5.0
                            while time.time() < wait_until:
                                line = read_serial()
                                if not line:
                                    continue
                                if line.startswith("Request credentials."):
                                    logger.info("Found ESP on serial.")
                                    send_messages("info", "ESP gefunden!")
                                    file = read()
                                    esp_data = file["esp_data"]
                                    esp_data["esp_port"] = esp_port.device
                                    file["esp_data"] = esp_data
                                    save(file)
                                    send_credentials()
                                    time.sleep(1)
                                    get_ip_thread()
                                    break
                                result = get_ip()
                                if result:
                                    break
                        except Exception as e:
                            logger.error(f"Serial connection error: {e}")
                            #return f"Error by serial connection: {e}"
                    time.sleep(5)
            else:
                time.sleep(1)
        else:
            time.sleep(5)


def start_get_port():
    thread = threading.Thread(target=get_port, daemon=True)
    thread.start()
    return

def send_credentials():
    file = read()
    esp_data = file["esp_data"]
    ssid = esp_data["ssid"]
    password = esp_data["password"]
    msg = f"WIFI:{ssid},{password}"
    send_serial(msg)
    logger.info("Sent WIFI credentials to ESP.")
    return

def get_ip():
    send_serial("GET_IP")
    time.sleep(0.05)
    line = read_serial()
    if line and line.startswith("IP address:"):
        file = read()
        esp_data = file["esp_data"]
        line_splitted = line.split(":")
        esp_data["ip"] = line_splitted[1]
        file["esp_data"] = esp_data
        save(file)
        global_variables.handshake = True
        logger.info("Received ESP IP.")
        # send_messages("info", f"IP erhalten: {line_splitted[1]}")
        # send_socket("status_message", "connected")
        return True

    return False

def get_ip_thread():
    logger.info("Try to get ESP IP.")
    while True:
        result = get_ip()
        if result:
            break
        else:
            time.sleep(0.5)
            continue
    return


def send_serial(msg):
    global ser
    if ser and ser.is_open:
        ser.write((msg + "\n").encode())
        send_messages("sent", msg) #Write on serial debug website
    return


def read_serial():
    global ser
    if not ser or not ser.is_open:
        return None

    line = ser.readline()
    if line:
        msg = line.decode("utf-8", errors="ignore").strip()
        if msg:
            send_messages("received", msg) #Write on serial debug website
            return msg
    return None
