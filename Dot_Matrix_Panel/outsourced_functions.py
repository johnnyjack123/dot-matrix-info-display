import json
import os
import Dot_Matrix_Panel.safe_shutil as shutil
from Dot_Matrix_Panel.safe_shutil import _check_path
from uuid import uuid4
import threading

import Dot_Matrix_Panel.global_variables as global_variables
from Dot_Matrix_Panel.sockets import send_socket
from Dot_Matrix_Panel.logger import logger
import requests

userdata_file_path = "userdata.json"

count = 0

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
            "userdata": global_variables.userdata_dict,
            "esp_data": global_variables.esp_data_dict,
            "server_data": global_variables.server_data_dict
        }
        with open("userdata.json", "w", encoding="utf-8") as file:
            json.dump(entry, file, ensure_ascii=False, indent=4)
    else:
        return

def create_folders():
    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    tmp_launcher_folder = os.path.join("tmp", "launcher")
    if not os.path.exists(tmp_launcher_folder):
        os.makedirs(tmp_launcher_folder)

    tmp_old_files = os.path.join("tmp", "old_files")
    if not os.path.exists(tmp_old_files):
        os.makedirs(tmp_old_files)

    tmp_old_files_launcher = os.path.join("tmp", "old_files", "launcher")
    if not os.path.exists(tmp_old_files_launcher):
        os.makedirs(tmp_old_files_launcher)

    tmp_old_files_main = os.path.join("tmp", "old_files", "main")
    if not os.path.exists(tmp_old_files_main):
        os.makedirs(tmp_old_files_main)
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

def deep_update_with_defaults(entry: dict, defaults: dict) -> dict:
    """Rekursiv Defaults in Entry mergen, ohne bestehende Werte zu überschreiben."""
    global count
    for key, default_value in defaults.items():
        if key not in entry:
            entry[key] = default_value
            count += 1
        elif isinstance(default_value, dict) and isinstance(entry[key], dict):
            deep_update_with_defaults(entry[key], default_value)
    return entry


def update_config_with_defaults(data: dict, defaults: dict) -> dict:
    """
    Aktualisiert JSON-Daten rekursiv:
    - Listen (z. B. userdata, backup_paths) werden über alle Einträge gemerged
    - Dicts (z. B. server_data) werden rekursiv zusammengeführt
    """
    global count
    for key, default_schema in defaults.items():
        if key not in data:
            data[key] = default_schema
            count += 1
        elif isinstance(data[key], list) and isinstance(default_schema, dict):
            for entry in data[key]:
                deep_update_with_defaults(entry, default_schema)
        elif isinstance(data[key], dict) and isinstance(default_schema, dict):
            deep_update_with_defaults(data[key], default_schema)
    return data

def migrate_config():
    global count, userdata_file_path
    """Lädt Config, migriert sie und speichert sie zurück"""

    # Defaults zusammenstellen
    defaults = {
        "userdata": global_variables.userdata_dict,
        "esp_data": global_variables.esp_data_dict,
        "server_data": global_variables.server_data_dict
    }

    # JSON laden
    with open(userdata_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Schema-Update durchführen (NEUE Funktion!)
    updated_data = update_config_with_defaults(data, defaults)

    # Zurückschreiben
    with open(userdata_file_path, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=4, ensure_ascii=False)

    if count > 0:
        logger.info(f"File successfully merged. {count} entries changed.")
    else:
        logger.info("Nothing merged in userdata file.")
    return updated_data

def check_for_updates(url_version, file_name, update):
    new_version_file = os.path.join("tmp", file_name)
    result = get_file(url_version, new_version_file)
    if result:
        try:
            if update == "launcher":
                version_file = file_name
            elif update == "main":
                version_file = os.path.join("Dot_Matrix_Panel", file_name)
            else:
                return f"Wrong update mode set: {update}."

            if not os.path.exists(version_file):
                with open(version_file, "w", encoding="utf-8") as f:
                    f.write("0.0")

            with open(version_file, "r", encoding="utf-8") as file:
                program_version = float(file.read().strip())
            with open(new_version_file, "r", encoding="utf-8") as file:
                new_version = float(file.read().strip())
            if new_version > program_version:
                return "Update"
            else:
                print("Program is up to date")
                logger.info("Program is up to date")
                return "Launch"
        except Exception as e:
            logger.error(f"No {file_name} available.")
            return "Update"
    else:
        return "Launch"

def get_file(url, save_path):
    response_version = requests.get(url)
    if response_version.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response_version.content)
            logger.info(f"{save_path} stored in /tmp")
            return True
    else:
        logger.error(f"File {save_path} is unreachable on repo {global_variables.repo} and branch {global_variables.branch}.")
        return False

def update_launcher():
    file = read()
    server_data = file["server_data"]
    branch = server_data["update_branch"]
    repo = server_data["update_repo"]
    url_launcher_py = f"https://raw.githubusercontent.com/{repo}/refs/heads/{branch}/launcher.py"
    url_launcher_bat = f"https://raw.githubusercontent.com/{repo}/refs/heads/{branch}/launcher.bat"
    tmp_launcher_folder = os.path.join("tmp", "launcher")
    launcher_py_path = os.path.join(tmp_launcher_folder, "launcher.py")
    launcher_bat_path = os.path.join(tmp_launcher_folder, "launcher.bat")
    launcher_py_old_path = os.path.join("tmp", "old_files", "launcher", "launcher.py")
    launcher_bat_old_path = os.path.join("tmp", "old_files", "launcher", "launcher.bat")
    result = get_file(url_launcher_py, launcher_py_path)
    if not result:
        return False
    result = get_file(url_launcher_bat, launcher_bat_path)
    if not result:
        return False

    try:
        shutil.move("launcher.py", launcher_py_old_path)
        shutil.move("launcher.bat", launcher_bat_old_path)
    except PermissionError as e:
        logger.error(f"Unable to move old launcher files: {e}")

    try:
        shutil.move(launcher_py_path, "launcher.py")
        shutil.move(launcher_bat_path, "launcher.bat")
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        shutil.move(launcher_py_old_path, "launcher.py")
        shutil.move(launcher_bat_old_path, "launcher.bat")


    logger.info("Launcher successfully updated.")
    new_launcher_version_path = os.path.join("tmp", "launcher_version.txt")
    for path in [launcher_py_old_path, launcher_bat_old_path, "launcher_version.txt"]:
        _check_path(path)
        os.remove(path)

    shutil.move(new_launcher_version_path, "launcher_version.txt")
    logger.info("Old files deleted.")
    return

def check_for_update_launcher():
    file = read()
    server_data = file["server_data"]
    branch = server_data["update_branch"]
    repo = server_data["update_repo"]
    url_version = f"https://raw.githubusercontent.com/{repo}/refs/heads/{branch}/launcher_version.txt"
    file_name = "launcher_version.txt"
    update = "launcher"
    result = check_for_updates(url_version, file_name, update)
    if result == "Update":
        logger.info("Update program launcher.")
        print("Update program launcher.")
        update_launcher()
    elif result == "Launch":
        logger.info("Launcher is up to date.")
    else:
        logger.error(f"Error in update process: {result}")
