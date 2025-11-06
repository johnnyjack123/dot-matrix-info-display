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
from Dot_Matrix_Panel.outsourced_functions import read, migrate_config, create_userdata, check_for_updates, create_folders
from Dot_Matrix_Panel.logger import logger

def check_internet_connection(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False

def update():
    print("Updating...")
    branch = "master"
    repo = "johnnyjack123/dot-matrix-info-display"
    folder_to_extract = "Dot_Matrix_Panel"
    target_folder = "./Dot_Matrix_Panel"

    # 1. ZIP vom GitHub-Branch herunterladen
    zip_url = f"https://github.com/{repo}/archive/refs/heads/{branch}.zip"
    print(f"🔄 Load ZIP from: {zip_url}")
    response = requests.get(zip_url)

    if response.status_code != 200:
        print(f"❌ Download error: {response.status_code}")
        return

    # 2. ZIP im Arbeitsspeicher entpacken
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
        extracted_dirname = zip_ref.namelist()[0].split("/")[0]  # z.B. "dot-matrix-info-display-Thread-Monitoring"
        print(f"📁 ZIP contents root directory: {extracted_dirname}")

        # 3. Temporär entpacken
        tmp_dir = "_tmp_update_dir"
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir, exist_ok=True)

        zip_ref.extractall(tmp_dir)

    # 4. Pfad zum zu extrahierenden Ordner
    source_folder = os.path.join(tmp_dir, extracted_dirname, folder_to_extract)

    if not os.path.exists(source_folder):
        print(f"❌ Folder '{folder_to_extract}' not found in ZIP!")
        return

    # 5. Zielordner ggf. löschen
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)

    # 6. Ordner verschieben
    shutil.move(source_folder, target_folder)
    print(f"✅ '{folder_to_extract}' was extracted in '{target_folder}'.")

    # 7. Aufräumen
    shutil.rmtree(tmp_dir)
    print("🧹 Remove temporary files.")
    launch_app()

def launch_app():
    subprocess.Popen(["python", "Dot_Matrix_Panel/Dot-Matrix_Main.py"])
    logger.info("Exit launcher.")
    sys.exit()

create_userdata()
create_folders()
migrate_config()
file = read()
userdata = file["userdata"]
auto_update = userdata["auto_update"]
if check_internet_connection() and auto_update == "yes":
    print("Internet connection")
    url_version = "https://raw.githubusercontent.com/johnnyjack123/dot-matrix-info-display/refs/heads/master/Dot_Matrix_Panel/version.txt"
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
