import requests
import subprocess
import zipfile
import io
import os
import shutil
import sys

def check_internet_connection(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False

def update():
    print("Updating...")
    branch = "Master"
    repo = "johnnyjack123/dot-matrix-info-display"
    folder_to_extract = "Dot-Matrix_Panel"
    target_folder = "./Dot-Matrix_Panel"

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
    subprocess.run([sys.executable, "Dot-Matrix_Panel/Dot-Matrix_Main.py"])

def check_for_updates():
    url_version = "https://raw.githubusercontent.com/johnnyjack123/dot-matrix-info-display/refs/heads/master/Dot-Matrix_Panel/version.txt"
    path_version = r"tmp\newest_version.txt"
    folder = os.path.dirname(path_version)
    if not os.path.exists(folder):
        os.makedirs(folder)
    response_version = requests.get(url_version)

    if response_version.status_code == 200:
        with open(path_version, "wb") as file:
            file.write(response_version.content)
            print("File stored in /tmp")
        try:
            with open("Dot-Matrix_Panel/version.txt", "r", encoding="utf-8") as file:
                program_version = float(file.read().strip())
            with open("tmp/newest_version.txt", "r", encoding="utf-8") as file:
                new_version = float(file.read().strip())
            if new_version > program_version:
                update()
            else:
                print("Program is up to date")
                launch_app()
        except Exception as e:
            print("No version.txt available.")
            update()
    else:
        print("Program is unreachable")

if check_internet_connection():
    print("Internet connection")
    check_for_updates()
else:
    print("No internet connection")
    launch_app()
