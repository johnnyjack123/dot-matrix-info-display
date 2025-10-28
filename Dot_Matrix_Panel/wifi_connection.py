import socket
import unidecode
import time
import threading

from Dot_Matrix_Panel.outsourced_functions import read, save, calculate_messsage_length
import Dot_Matrix_Panel.global_variables as global_variables

messages = []

def collect_messages(value: str):
    global messages
    messages.append(value)

def send():
    global messages
    print("send")
    actual_screen = global_variables.screen
    wifi_port = 1234
    while True:
        file = read()
        esp_data = file["esp_data"]

        if esp_data:  # Sicherstellen, dass die Liste nicht leer ist
            esp_ip = esp_data["ip"]  # letzter gespeicherter IP-Eintrag
            print("ESP IP:", esp_ip)
            if esp_data["ip"]:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((esp_ip, wifi_port))
                    print("Connected with ESP")
                    global_variables.connected = True
                    while True:
                        time.sleep(0.1)
                        if len(messages) != 0:
                            messages.reverse()
                            message: str = str(messages.pop())
                            messages.reverse()
                            print(f"Raw message: {message}")
                            mode, value = message.strip().split(",", 1)
                            actual_screen = mode
                            ascii_message = unidecode.unidecode(value)
                            if not mode == "Clock" or not mode == "Timer" or not mode == "Weather":
                                message_length = calculate_messsage_length(ascii_message)
                                new_message = mode + "," + message_length
                                s.sendall((new_message + "\n").encode("ascii"))
                                print("Message: " + new_message)
                            else:
                                s.sendall((message + "\n").encode("ascii"))
                                print("Message: " + message)
                            time.sleep(2)
            else:
                print("No ip")
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
    file = read()
    esp_data = file["esp_data"]
    if esp_data["ip"]:
        if not global_variables.send_thread:
            global_variables.send_thread = True
            thread = threading.Thread(target=send, daemon=True)
            thread.start()