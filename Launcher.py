import requests
import subprocess

def check_internet_connection(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False

def update():
    print("updating")
    url_py = "https://raw.githubusercontent.com/johnnyjack123/dot-matrix-info-display/refs/heads/Thread-Monitoring/Dot-Matrix_Main.py"
    path_py = r".\tmp\newest_version.py"
    response_py = requests.get(url_py)

    if response_py.status_code == 200:
        with open(path_py, "wb") as file:
            file.write(response_py.content)
            print("File stored in /tmp")

def launch_app():
    subprocess.run([r"C:\Users\jonat\Documents\Programmieren\Dot-Matrix-Panel\venv\Scripts\python.exe", "Dot-Matrix_Panel/Dot-Matrix_Main.py"])

if check_internet_connection():
    print("Internet connection")
    url_version = "https://raw.githubusercontent.com/johnnyjack123/dot-matrix-info-display/refs/heads/Thread-Monitoring/version.txt"
    path_version = r"Dot-Matrix_Panel\tmp\newest_version.txt"
    response_version = requests.get(url_version)

    if response_version.status_code == 200:
        with open(path_version, "wb") as file:
            file.write(response_version.content)
            print("File stored in /tmp")
        with open("Dot-Matrix_Panel/version.txt", "r", encoding="utf-8") as file:
            program_version = float(file.read().strip())
        with open("Dot-Matrix_Panel/tmp/newest_version.txt", "r", encoding="utf-8") as file:
            new_version = float(file.read().strip())
        if new_version > program_version:
            update()
        else:
            print("Program is up to date")
            launch_app()
    else:
        print("File is unreachable")

else:
    print("No internet connection")
    launch_app()
