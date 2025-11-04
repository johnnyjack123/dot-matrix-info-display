import json
import os
from uuid import uuid4
import threading
import global_variables as global_variables
from sockets import send_socket

userdata_file_path = "userdata.json"

def save(data):
    global userdata_file_path
    try:
        with open(userdata_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Can´t save userdata.json file. Error: {e}")

def read():
    global userdata_file_path
    try:
        with open(userdata_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Can´t open userdata.json file. Error: {e}")

def calculate_messsage_length(ascii_message):
    char_sizes = {}
    length = 0
    pixel_amount = 62
    with open("Dot_Matrix_Panel/character_size.csv", "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(",")
            if len(parts) >= 3:
                char = parts[0]
                width = int(parts[1])
                height = int(parts[2])
                char_sizes[char] = (width, height)

        for letter in ascii_message:
            if letter in char_sizes:
                width, height = char_sizes[letter]
                length = length + width + 1 #Sum all lengths, for space between letters + 1
            else:
                length = length + 5

        if length > pixel_amount:
            for x in ascii_message:
                last_letter = ascii_message[-1]
                width, height = char_sizes.get(last_letter, (4, 7))
                length = length - width - 1
                ascii_message = ascii_message[:-1]
                if length <= pixel_amount:
                    ascii_message = ascii_message + "."
                    break
        return ascii_message

def create_userdata():
    if not os.path.exists("userdata.json"):
        entry = {
            "userdata": {
                "username": "",
                "weather_api_key": "",
                "city": "",
                "open": "App"
            },
            "esp_data": {
                "ip": "",
                "ssid": "",
                "password": "",
                "esp_port": ""
            },
            "server_data": {
                "secret_key": ""
            }
        }
        with open("userdata.json", "w", encoding="utf-8") as file:
            json.dump(entry, file, ensure_ascii=False, indent=4)
            app_window = "App"
    else:
        return

def get_secret_key():
    file = read()
    server_data = file["server_data"]
    if not server_data["secret_key"]:
        secret_key = str(uuid4())
        server_data["secret_key"] = secret_key
        file["server_data"] = server_data
        save(file)
    else:
        secret_key = server_data["secret_key"]
    return secret_key

def check_connection():
    while True:
        if not global_variables.connected:
            send_socket("connected", False)
            send_socket("status_message", "Trying to connect to the ESP. This can take a little while.")
        else:
            send_socket("connected", True)
            send_socket("status_message", "Successfully connected to your ESP. Please restart this program now.")

def start_get_port():
    thread = threading.Thread(target=check_connection(), daemon=True)
    thread.start()