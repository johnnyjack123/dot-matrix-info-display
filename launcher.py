import os
import sys

# Pfad zum Projektverzeichnis hinzufügen
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Pfad zum Dot_Matrix_Panel-Ordner hinzufügen
dot_matrix_dir = os.path.join(project_dir, "Dot_Matrix_Panel")
sys.path.insert(0, dot_matrix_dir)

import Dot_Matrix_Panel.global_variables as global_variables
global_variables.project_dir = project_dir

import requests
import subprocess
import zipfile
import io
import Dot_Matrix_Panel.safe_shutil as shutil
from Dot_Matrix_Panel.outsourced_functions import read, migrate_config, create_userdata, check_for_updates, create_folders
from Dot_Matrix_Panel.logger import logger

logger.info(f"Project directory: {project_dir}")
def check_internet_connection(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False


def safe_replace_folder(source_folder, target_folder):
    """
    Ersetzt den Zielordner nur, wenn das Kopieren erfolgreich war.
    """
    backup_folder = f"{target_folder}_old"
    new_folder = f"{target_folder}_new"

    # Falls alte Backups existieren
    for folder in (backup_folder, new_folder):
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)

    try:
        # 1️⃣ Neue Version in temporären Ordner kopieren
        shutil.copytree(source_folder, new_folder)
        logger.info("Copied new version to temp folder.")

        # 2️⃣ Teste, ob wichtige Dateien vorhanden sind
        must_have = ["version.txt", "Dot-Matrix_Main.py"]
        for f in must_have:
            if not os.path.exists(os.path.join(new_folder, f)):
                raise FileNotFoundError(f"Required file missing: {f}")

        # 3️⃣ Alte Version sichern
        if os.path.exists(target_folder):
            try:
                os.rename(target_folder, backup_folder)
                logger.info("Renamed old folder to backup.")
            except PermissionError:
                logger.error("Cannot rename old folder (file in use). Update aborted.")
                shutil.rmtree(new_folder, ignore_errors=True)
                return False

        # 4️⃣ Neue Version aktivieren
        os.rename(new_folder, target_folder)
        logger.info("Activated new version successfully.")

        # 5️⃣ Alte Version löschen
        shutil.rmtree(backup_folder, ignore_errors=True)
        logger.info("Removed old backup.")
        return True

    except Exception as e:
        logger.error(f"Update failed: {e}")
        # Im Fehlerfall: Rückfall auf alte Version
        if os.path.exists(backup_folder) and not os.path.exists(target_folder):
            os.rename(backup_folder, target_folder)
            logger.warning("Restored old version due to update failure.")
        shutil.rmtree(new_folder, ignore_errors=True)
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

    # 1. ZIP vom GitHub-Branch herunterladen
    zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    print(f"Load ZIP from: {zip_url}")
    response = requests.get(zip_url)

    if response.status_code != 200:
        print(f"Download error: {response.status_code}")
        logger.error(f"Download error: {response.status_code}")
        return

    # 2. ZIP im Arbeitsspeicher entpacken
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        extracted_dirname = zip_ref.namelist()[0].split("/")[0]  # z.B. "dot-matrix-info-display-Thread-Monitoring"
        print(f"ZIP contents root directory: {extracted_dirname}")

        # 3. Temporär entpacken
        tmp_dir = "_tmp_update_dir"
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

        os.makedirs(tmp_dir, exist_ok=True)

        zip_ref.extractall(tmp_dir)
        logger.info("Extracted update in tmp dir.")
    source_folder = os.path.join(tmp_dir, extracted_dirname, folder_to_extract)

    if not os.path.exists(source_folder):
        print(f"Folder '{folder_to_extract}' not found in ZIP!")
        logger.error(f"Folder '{folder_to_extract}' not found in ZIP!")
        return

    #old_main_path = os.path.join("tmp", "old_files", "main")

    if os.path.exists(target_folder):
        update_successful = safe_replace_folder(source_folder, target_folder)
        if not update_successful:
            logger.error("Update aborted, old version restored.")
            print("Update aborted, old version restored.")
            launch_app()
        else:
            logger.info("Update successfully installed.")
            print("Update successfully installed.")
    else:
        logger.error("Target folder doesn´t exists.")
    launch_app()


def launch_app():
    python_executable = sys.executable  # das ist der aktuell laufende/interaktive venv-Python
    subprocess.Popen([
        python_executable,
        "-m", "Dot_Matrix_Panel.Dot-Matrix_Main",
        "--project-dir", os.path.abspath(".")
    ])
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
        logger.info("Update main program...")
        print("Update main program...")
        update()
    elif result == "Launch":
        logger.info("Program is up to date.")
        print("Program is up to date.")
        launch_app()
    else:
        logger.error(f"Error in update process: {result}")
else:
    print("No internet connection or auto updates disabled.")
    launch_app()
