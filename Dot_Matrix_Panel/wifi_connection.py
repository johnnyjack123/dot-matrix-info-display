import socket
import unidecode
import time
import threading

from Dot_Matrix_Panel.outsourced_functions import read, save, calculate_messsage_length
from Dot_Matrix_Panel.sockets import send_socket
import Dot_Matrix_Panel.global_variables as global_variables
from Dot_Matrix_Panel.logger import logger

messages = []

def collect_messages(value: str):
    global messages
    messages.append(value)

def send():
    global messages
    wifi_port = 1234
    while True:
        file = read()
        esp_data = file["esp_data"]

        if esp_data:  # Sicherstellen, dass die Liste nicht leer ist
            esp_ip = esp_data["ip"]  # letzter gespeicherter IP-Eintrag
            logger.info(f"ESP IP: {esp_ip}")
            if esp_data["ip"]:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(10)
                        s.connect((esp_ip, wifi_port))
                        logger.info("Connected with ESP")
                        global_variables.connected = True
                        send_socket('esp_connection_status', {'connected': True})
                        while True:
                            time.sleep(0.1)
                            if len(messages) != 0:
                                messages.reverse()
                                message: str = str(messages.pop())
                                messages.reverse()
                                mode, value = message.strip().split(",", 1)
                                global_variables.screen = mode
                                ascii_message = unidecode.unidecode(value)
                                if mode == "Music" or mode == "Tasks" or mode == "Simhub":
                                    print(f"Message: {message}, mode: {mode}, if")
                                    message_length = calculate_messsage_length(ascii_message)
                                    new_message = mode + "," + message_length
                                    print(f"Shorted message: {new_message}")
                                    s.sendall((new_message + "\n").encode("ascii"))
                                elif mode == "Clock" or mode == "Timer" or mode == "Weather":
                                    s.sendall((message + "\n").encode("ascii"))
                                    print(f"Message: {message}, mode: {mode}, else")
                                time.sleep(2)
                except Exception as e:
                    logger.error(f"Error in WIFI connection: {e}")
            else:
                time.sleep(1)
        else:
            print("No userdata available")
            time.sleep(1)

                    #TODO Checking Connection
                    #try:
                        #s.sendall(("Connection,Connection" + "\n").encode("ascii"))
                        #data = b""
                        #while not data.endswith(b'\n'):
                            #part = s.recv(1024)
                            #if not part:
                                #break
                            #data += part

                        #print("Answer from ESP:", data.decode("utf-8").strip())
                        #if data.decode("utf-8").strip():
                            #connection = True
                        #else:
                            #connection = False
                        #print("Connection: " + str(connection))

                    #except Exception as e:
                        #connection = True
                        #print("Connection: " + str(connection))

def start_send():
    if not global_variables.send_thread:
        global_variables.send_thread = True
        thread = threading.Thread(target=send, daemon=True)
        thread.start()