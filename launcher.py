import os
import sys

# Pfad zum Projektverzeichnis hinzufügen
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Pfad zum Dot_Matrix_Panel-Ordner hinzufügen
dot_matrix_dir = os.path.join(project_dir, "Dot_Matrix_Panel")
sys.path.insert(0, dot_matrix_dir)

import requests
import subprocess
import zipfile
import io
import shutil
from Dot_Matrix_Panel.outsourced_functions import read, migrate_config, create_userdata, check_for_updates, create_folders, check_file_access
from Dot_Matrix_Panel.logger import logger
import Dot_Matrix_Panel.global_variables as global_variables

global_variables.project_dir = project_dir
logger.info(f"Project directory: {project_dir}")
def check_internet_connection(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False

def update():
    print("Updating...")
    logger.info("Updating...")

    file = read()
    server_data = file["server_data"]
    branch = server_data["update_branch"]
    repo = server_data["update_repo"]

    folder_to_extract = "Dot_Matrix_Panel"
    target_folder = "Dot_Matrix_Panel"
    state = True

    # 1. ZIP vom GitHub-Branch herunterladen
    zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    print(f"🔄 Load ZIP from: {zip_url}")
    response = requests.get(zip_url)

    if response.status_code != 200:
        print(f"❌ Download error: {response.status_code}")
        logger.error(f"❌ Download error: {response.status_code}")
        return

    # 2. ZIP im Arbeitsspeicher entpacken
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        extracted_dirname = zip_ref.namelist()[0].split("/")[0]  # z.B. "dot-matrix-info-display-Thread-Monitoring"
        print(f"📁 ZIP contents root directory: {extracted_dirname}")

        # 3. Temporär entpacken
        tmp_dir = "_tmp_update_dir"
        if os.path.exists(tmp_dir):
            try:
                check_file_access(tmp_dir)
                shutil.rmtree(tmp_dir)
            except PermissionError  as e:
                logger.error(f"Permission error: {e}")

        os.makedirs(tmp_dir, exist_ok=True)

        zip_ref.extractall(tmp_dir)
        logger.info("Extracted update in tmp dir.")
    source_folder = os.path.join(tmp_dir, extracted_dirname, folder_to_extract)

    if not os.path.exists(source_folder):
        print(f"❌ Folder '{folder_to_extract}' not found in ZIP!")
        logger.error(f"❌ Folder '{folder_to_extract}' not found in ZIP!")
        return

    old_main_path = os.path.join("tmp", "old_files", "main")

    if os.path.exists(target_folder):
        try:
            check_file_access(target_folder)
            check_file_access(old_main_path)
            shutil.move(target_folder, old_main_path)
            logger.info("Moved old version in tmp.")
        except Exception as e:
            state = False
            logger.error(f"Error in moving old version of main folder: {e}. Program stays on old version.")
        if not state:
            pass
        else:
            try:
                check_file_access(source_folder)
                check_file_access(target_folder)
                shutil.move(source_folder, target_folder)
                logger.info("Moved new version in root directory.")
            except Exception as e:
                check_file_access(source_folder)
                check_file_access(target_folder)
                shutil.move(old_main_path, target_folder)
                logger.error(f"Error in moving new version of main folder: {e}. Programm stays on old version.")
            if not state:
                pass
            else:
                try:
                    old_main_dir_path = os.path.join("tmp", "old_files", "main")
                    check_file_access(tmp_dir)
                    check_file_access(old_main_dir_path)
                    shutil.rmtree(tmp_dir)
                    shutil.rmtree(old_main_dir_path)
                    print("🧹 Remove temporary files.")
                    logger.info("Removed old version.")
                except PermissionError as e:
                    logger.error(f"Permission error: {e}")
    else:
        logger.error("Target folder doesn´t exists.")
    launch_app()


def launch_app():
    python_executable = sys.executable  # das ist der aktuell laufende/interaktive venv-Python
    script_path = os.path.join("Dot_Matrix_Panel", "Dot-Matrix_Main.py")
    subprocess.Popen([python_executable, script_path])
    logger.info("Exit launcher.")
    sys.exit()

create_userdata()
create_folders()
migrate_config()
file = read()
userdata = file["userdata"]
auto_update = userdata["auto_update"]
server_data = file["server_data"]
if check_internet_connection() and auto_update == "yes":
    print("Internet connection")
    branch = server_data["update_branch"]
    repo = server_data["update_repo"]
    url_version = f"https://raw.githubusercontent.com/{repo}/refs/heads/{branch}/Dot_Matrix_Panel/version.txt"
    file_name = "version.txt"
    update_mode = "main"
    result = check_for_updates(url_version, file_name, update_mode)
    if result == "Update":
        logger.info("Update main program.")
        update()
    elif result == "Launch":
        launch_app()
    else:
        logger.error(f"Error in update process: {result}")
else:
    print("No internet connection or auto updates disabled.")
    launch_app()
