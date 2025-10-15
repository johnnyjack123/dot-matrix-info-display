import serial
from serial.tools import list_ports
from datetime import datetime
import time

from flask import Flask, render_template, request, redirect, url_for, jsonify
import webview
import threading
import requests
import json
import socket
import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
import serial.tools.list_ports
import unidecode
import os
import webbrowser

app = Flask(__name__)

@app.route('/')
def index():
    stop_clock()
    stop_weather()
    stop_music()

    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if data.get("userdata") and any("username" in user for user in data["userdata"]):
            return redirect(url_for("connect"))
        else:
            return render_template("landing.html")


baud_rate = 9600

running_clock = False
clock_thread = None

music_thread_started = False
weather_thread_started = False
timer_thread = False
task_thread = False
send_thread = False
monitoring_thread = False
rounded_temperature = ""

now = [1, 2, 3, 4, 5, 6]

state_timer = False

hours = ""
minutes = ""
seconds = ""

note = ""
remind_time = ""
task_collection = {}

messages = []

json_structure = {"userdata": []}

last_song = ""

transmission_method = ""

title = ""
current_title = ""

running_threads = []
sleeping_threads = []

esp_ip = ""
port = 1234

connection = True #State variable to check if esp is connected or not

@app.route('/initial_connect', methods=["GET"])
def initial_connect():
    text = ""
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    user = data["userdata"][0]

    if user.get("ip", "") == "":
        ports = list_ports.comports()
        print(f"Ports: {ports}")
        if not ports:
            return "No ESP found"
        for esp_port in ports:
            message = ""

            try:
                print(f"ESP port interface: {esp_port.device}")
                ser = serial.Serial(esp_port.device, baud_rate, timeout=5)
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                ser.write(b"GET_IP\n")
                #time.sleep(0.05)
                wait_until = time.time() + 5.0
                while time.time() < wait_until:
                    line = ser.readline()
                    if not line:
                        # nichts empfangen, weiter versuchen bis Timeout
                        continue

                    try:
                        message = line.decode("utf-8", errors="ignore").strip()
                    except Exception:
                        message = line.decode(errors="ignore").strip()

                    print(f"Antwort von {esp_port.device}: '{message}'")
                    if message:
                        break

                if message and message.startswith("192."):
                    ser.close()
                    user["ip"] = message
                    data["userdata"][0] = user

                    with open("userdata.json", "w", encoding="utf-8") as file:
                        json.dump(data, file, ensure_ascii=False, indent=4)
                        text = "Connected successfully. Please restart the program now."
                    break
                else:
                    print(f"Keine IP-Antwort auf {esp_port.device}, weiter zum nächsten Port.")

            except Exception as e:
                return f"Error by serial connection: {e}"

    return render_template("success.html", text=text)

@app.route('/connect', methods=["POST", "GET"])
def connect():
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        user = data["userdata"][0]

        if not user["ip"]:
            connection_state = True
        else:
            connection_state = False

    return render_template("connect.html", connection_state=connection_state)

@app.route('/check_connection')
def check_connection():
    global esp_ip, port
    try:
        with open("userdata.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            userdata = data["userdata"][0]
            if userdata:
                esp_ip = userdata["ip"]
            else:
                return jsonify({"connected": False})

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # max. 1 Sekunde warten
            s.connect((esp_ip, port))
            start_get_time()
            start_send()
            start_thread_monitoring()
            return jsonify({"connected": True})
    except Exception as e:
        start_get_time()
        start_send()
        start_thread_monitoring()
        return jsonify({"connected": False})


@app.route('/dashboard')
def dashboard():
    stop_clock()
    stop_weather()
    stop_music()
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if data.get("userdata") and any("username" in user for user in data["userdata"]):
            userdata = data.get("userdata", [])
            username = userdata[-1]["username"]
            return render_template('dashboard.html', username=username)
        else:
            return render_template("landing.html")

@app.route('/clock')
def clock():
    global now
    start_clock()
    stop_weather()
    stop_music()
    return render_template('clock.html', year=now[0], month=now[1], day=now[2], hour=now[3], minute=now[4])

@app.route('/stop_clock')
def stop_clock_route():
    stop_clock()
    return redirect(url_for('index'))

@app.route('/timer', methods=['GET', 'POST'])
def timer_page():
    global hours, minutes, seconds
    stop_clock()
    stop_weather()
    stop_music()
    if not state_timer:
        if request.method == 'POST':
            hours = request.form['hours']
            minutes = request.form['minutes']
            seconds = request.form['seconds']
            timer_time = hours + "/" + minutes + "/" + seconds
            message = f"Timer,{timer_time}"
            collect_messages(message)
            start_timer()
            return render_template('timer.html', sent_time=timer_time)
    else:
        timer_time = str(hours) + "/" + str(minutes) + "/" + str(seconds)
        message = f"Timer,{timer_time}"
        collect_messages(message)
    return render_template('timer.html', sent_time=None)

@app.route('/music')
def music():
    global title
    stop_clock()
    stop_weather()
    start_music()
    time.sleep(0.2)
    send_music(title)
    print("Title: " + title)
    return render_template('music.html', title=title)

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    global note, remind_time, task_thread, task_collection
    if request.method == 'POST':
        if request.method == 'POST':
            if 'delete' in request.form:
                delete_time = request.form['delete']
                task_collection.pop(delete_time, None)
                print(task_collection)
            else:
                note = request.form['task']
                remind_time = str(request.form['remind_time'])
                if remind_time in task_collection:
                    return render_template('internal_server_error.html', error="Its not possible to create two tasks with the same time")
                task_collection[remind_time] = note
                task_thread = False
                print(type(remind_time), remind_time)
                start_tasks()
    return render_template('tasks.html', tasks=task_collection)

@app.route('/simhub')
def simhub():
    stop_clock()
    stop_weather()
    stop_music()
    return render_template('simhub.html')

@app.route('/weather')
def weather():
    stop_clock()
    stop_music()
    start_weather()
    time.sleep(0.4)
    return render_template('weather.html', temperature=rounded_temperature)

@app.route('/api/temperature')
def api_temperature():
    return jsonify({
        'temperature': str(rounded_temperature) + "°C"
    })

@app.route('/api/tasks')
def api_tasks():
    return jsonify(task_collection)

@app.route('/api/music')
def api_music():
    global title
    return jsonify({"title": title})

@app.route('/api/time')
def api_time():
    global now
    return jsonify({
        'day': now[2],
        'month': now[1],
        'year': now[0],
        'hour': f"{now[3]:02}",
        'minute': f"{now[4]:02}"
    })

@app.route('/api/threads')
def api_threads():
    global running_threads, sleeping_threads
    return jsonify({
        "running_threads": running_threads,
        "sleeping_threads": sleeping_threads
    })

@app.route('/api/connection')
def api_connection():
    global connection
    return jsonify({"connection": connection})

@app.route('/landing', methods=['GET', 'POST'])
def landing():
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Check if userdata is existing
    if "userdata" not in data:
        data["userdata"] = []

    # Add a new entry
    new_entry = {
        "username": request.form["username"],
        "ip": "",
        "weather_api_key": request.form.get("weather_api_key"),
        "city": request.form.get("city"),
        "open": "App"
    }

    data["userdata"].append(new_entry)

    # Save file
    with open("userdata.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    if data.get("userdata") and any("username" in user for user in data["userdata"]):
        return redirect(url_for("connect"))
    else:
        return render_template("landing.html")

@app.route('/manage_threads', methods=["POST", "GET"])
def manage_threads():
    global weather_thread_started, timer_thread, task_thread, send_thread, monitoring_thread, running_threads, sleeping_threads

    return render_template("thread_monitoring.html", running_threads=running_threads, sleeping_threads=sleeping_threads)

@app.route('/settings_page', methods=["POST", "GET"])
def settings_page():
    with open("./Dot-Matrix_Panel/version.txt", "r", encoding="utf-8") as file:
        version = "Version: " + str(file.read().strip())

        # Load file
        with open("userdata.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        if not data.get("userdata") or not isinstance(data["userdata"], list):
            data["userdata"] = [{}]

        # Takes the first user entry
        user = data["userdata"][0]
        app_window = user["open"]
        if app_window == "App":
            switch_state = True
        else:
            switch_state = False

        return render_template("settings.html", version=version, switch_state=switch_state)

@app.route('/settings', methods=["POST", "GET"])
def settings():
    switch_state = True
    with open("./Dot-Matrix_Panel/version.txt", "r", encoding="utf-8") as file:
        if request.method == "POST":
            username = request.form.get("username")
            esp_ip = request.form.get("ip")
            api_key = request.form.get("weather_api_key")
            city = request.form.get("city")
            switch = request.form.get("switch")

            # Load file
            with open("userdata.json", "r", encoding="utf-8") as file:
                data = json.load(file)

            if not data.get("userdata") or not isinstance(data["userdata"], list):
                data["userdata"] = [{}]

            # Takes the first user entry
            user = data["userdata"][0]

            if username:
                user["username"] = username
            if esp_ip:
                user["ip"] = esp_ip
            if api_key:
                user["weather_api_key"] = api_key
            if city:
                user["city"] = city

            if switch == "on":
                user["open"] = "App"
            else:
                user["open"] = "Browser"

            # Stelle sicher, dass NUR EIN Benutzer gespeichert wird
            data["userdata"] = [user]

            # Datei zurückschreiben
            with open("userdata.json", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        return redirect(url_for("settings_page"))

def start_timer():
    global timer_thread
    if not timer_thread:
        time.sleep(1.5)
        timer_thread = True
        thread = threading.Thread(target=timer, daemon=True)
        thread.start()

def stop_timer():
    global timer_thread
    timer_thread = False

def timer():
    global hours, minutes, seconds, state_timer
    while True:
        state_timer = True
        time.sleep(1)
        if int(seconds) > 0:
            seconds = int(seconds) - 1
        else:
            seconds = 59
            if int(minutes) > 0:
                minutes = int(minutes) - 1
            else:
                if int(hours) == 0:
                    print("Timer Stopped")
                    #ser.write("Timer,Break".encode('utf-8'))
                    collect_messages("Timer,Break")
                    stop_timer()
                    stop_music()
                    stop_weather()
                    stop_clock()
                    state_timer = False
                    break
                else:
                    minutes = 59
                    hours = int(hours) - 1

def start_tasks():
    global task_thread
    if not task_thread:
        task_thread = True
        thread = threading.Thread(target=tasks, daemon=True)
        thread.start()

def stop_tasks():
    global task_thread
    task_thread = False

def tasks():
    global now, task_thread, task_collection
    while True:
        if len(task_collection) > 0:
            # Über eine KOPIE des Dictionaries iterieren:
            for task_time, task in list(task_collection.items()):
                current_time = f"{now[3]:02}:{now[4]:02}"
                if task_time == current_time:
                    time.sleep(0.2)
                    #ascii_message = unidecode.unidecode(task)
                    #ascii_message = calculate_messsage_length(task)
                    message = "Notes," + task
                    collect_messages(message)
                    #print(message)
                    #print("Note sent")
                    #print(note_collection)
                    del task_collection[task_time]  # Sicheres Löschen
                    time.sleep(1)

                    if not len(task_collection) > 0:
                        stop_tasks()
                        stop_music()
                        stop_weather()
                        stop_clock()
                        return
                time.sleep(1)
        time.sleep(1)

def get_time():
    global now
    while True:
        global now
        date = datetime.now()
        year = date.year
        month = date.month
        day = date.day
        hour = date.hour
        minute = date.minute
        second = date.second

        now[0] = year
        now[1] = month
        now[2] = day
        now[3] = hour
        now[4] = minute
        now[5] = second

        time.sleep(1)

def start_get_time():
    thread = threading.Thread(target=get_time, daemon=True)
    thread.start()

def start_weather():
    global weather_thread_started
    if not weather_thread_started:
        weather_thread_started = True
        thread = threading.Thread(target=send_weather_loop, daemon=True)
        thread.start()

def stop_weather():
    global weather_thread_started
    weather_thread_started = False

def send_weather_loop():
    last_minute = ""
    count = 14
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if data.get("userdata") and any("username" in user for user in data["userdata"]):
            userdata = data["userdata"]
            for user in userdata:
                if "weather_api_key" in user and "city" in user:
                    API_KEY = user["weather_api_key"]
                    stadt = user["city"]
                    url = f"http://api.openweathermap.org/data/2.5/weather?q={stadt}&appid={API_KEY}&units=metric&lang=de"

        while weather_thread_started:
            global now
            if now[4] != last_minute:
                count = count + 1
                last_minute = now[4]
                print(count)
                if count == 15:
                    try:
                        answer = requests.get(url)
                        daten = answer.json()
                        if answer.status_code == 200:
                            global rounded_temperature
                            temperature = daten["main"]["temp"]
                            rounded_temperature = round(temperature, 1)
                            message = "Weather," + str(rounded_temperature)
                            collect_messages(message)
                            count = 0
                            print("New temperature set")
                        else:
                            print("Unable to get weather datas")
                            rounded_temperature = "Weather unavailable"
                    except Exception as e:
                        print("Unable to send message")
            else:
                time.sleep(1)


# Background function to get the time
def clock_loop():
    global now
    last_minute = -1
    global running_clock
    while running_clock:
        if now[4] != last_minute:
            message = f"Clock,{now[2]}/{now[1]}/{now[0]}/{now[3]}/{now[4]}"
            collect_messages(message)
            last_minute = now[4]
        time.sleep(1)

def start_clock():
    global running_clock, clock_thread
    if not running_clock:
        running_clock = True
        clock_thread = threading.Thread(target=clock_loop, daemon=True)
        clock_thread.start()

def stop_clock():
    global running_clock
    running_clock = False

def start_music():
    global music_thread_started
    if not music_thread_started:
        music_thread_started = True
        thread = threading.Thread(target=get_music, daemon=True)
        thread.start()

def stop_music():
    global music_thread_started, title, current_title
    music_thread_started = False
    title = ""
    current_title = ""

def get_music():
    global music_thread_started
    while music_thread_started:
        asyncio.run(get_song_info())
        time.sleep(2)

async def get_song_info():
    # Get the media session manager
    global last_song, title
    session_manager = await MediaManager.request_async()
    session = session_manager.get_current_session()
    if session:
        # Get the media properties
        media_properties = await session.try_get_media_properties_async()

        # Extract song information
        title = media_properties.title
        artist = media_properties.artist
        album = media_properties.album_title
        if str(title) != last_song:
            send_music(title)
            print(f"Title: {title}")
            print(f"Artist: {artist}")
            print(f"Album: {album}")
            last_song = str(title)
        time.sleep(1)
    else:
        print("No active media session found.")

def send_music(song):
    global current_title
    if title != "":
        if title != current_title:
            collect_messages("Music," + title)
            current_title = title

def start_send():
    global send_thread
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        userdata = data["userdata"][0]
    if userdata["ip"]:
        if not send_thread:
            send_thread = True
            thread = threading.Thread(target=send, daemon=True)
            thread.start()

def collect_messages(value: str):
    global messages
    messages.append(value)

def send():
    global messages, esp_ip, port, connection
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        userdata = data["userdata"]

        if userdata:  # Sicherstellen, dass die Liste nicht leer ist
            esp_ip = userdata[-1]["ip"]  # letzter gespeicherter IP-Eintrag
            print("ESP IP:", esp_ip)
        else:
            print("No userdata available")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((esp_ip, port))
            print("Connected with ESP")
            while True:
                time.sleep(0.1)
                if len(messages) != 0:
                    messages.reverse()
                    message: str = str(messages.pop())
                    messages.reverse()

                    mode, value = message.strip().split(",", 1)
                    ascii_message = unidecode.unidecode(value)
                    if not mode == "Clock" or mode == "Timer" or mode == "Weather":
                        message_length = calculate_messsage_length(ascii_message)
                        new_message = mode + "," + message_length
                        s.sendall((new_message + "\n").encode("ascii"))
                        print("Message: " + new_message)
                    else:
                        s.sendall((message + "\n").encode("ascii"))
                        print("Message: " + message)
                    time.sleep(2)
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

def calculate_messsage_length(ascii_message):
    char_sizes = {}
    length = 0
    pixel_amount = 62
    with open("./Dot-Matrix_Panel/character_size.csv", "r", encoding="utf-8") as file: #Path origin from Launcher.py script
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
                length = length + width + 1 #Sum all lengths, for space between letters + 1 TODO Leertaste mit hinzufügen
            else:
                length = length + 5


        print("Length: " + str(length))

        if length > pixel_amount:
            for x in ascii_message:
                last_letter = ascii_message[-1]
                width, height = char_sizes.get(last_letter, (4, 7))
                length = length - width - 1
                ascii_message = ascii_message[:-1]
                if length <= pixel_amount:
                    ascii_message = ascii_message + "."
                    print("New length: " + str(length))
                    break
        print("return")
        return ascii_message

def start_thread_monitoring():
    global monitoring_thread
    if not monitoring_thread:
        monitoring_thread = True
        thread = threading.Thread(target=thread_monitoring, daemon=True)
        thread.start()

def thread_monitoring():
    global weather_thread_started, timer_thread, task_thread, send_thread, monitoring_thread, running_threads, sleeping_threads
    while True:
        running_threads = []
        sleeping_threads = []
        threads = [{"name": "Weather", "value": weather_thread_started},
                   {"name": "Timer", "value": timer_thread},
                   {"name": "Tasks", "value": task_thread},
                   {"name": "Send", "value": send_thread},
                   {"name": "Thread Monitoring", "value": monitoring_thread},
                   {"name": "Music", "value": music_thread_started},
                   {"name": "Clock", "value": clock_thread}]
        for thread in threads:
            if thread["value"]:
                running_threads.append(thread["name"])
            else:
                sleeping_threads.append(thread["name"])
        time.sleep(3)

def find_esp_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        beschreibung = port.description.lower()
        if "ch340" in beschreibung or "silicon" in beschreibung or "cp210" in beschreibung or "usb serial" in beschreibung or "esp" in beschreibung or "arduino" in beschreibung:
            return port.device
    return None

def start_flask():
    app.run()

# Start
if __name__ == '__main__':

    if not os.path.exists("userdata.json"):
        with open("userdata.json", "w", encoding="utf-8") as file:
            json.dump({"userdata": []}, file, ensure_ascii=False, indent=4)
            app_window = "App"
    else:
        # Datei laden
        try:
            with open("userdata.json", "r", encoding="utf-8") as file:
                data = json.load(file)

            # Nimm nur den ersten Benutzer-Eintrag
            user = data["userdata"][0]
            app_window = user.get("open", "App")  # Standardwert falls nicht gesetzt
        except Exception as e:
            with open("userdata.json", "w", encoding="utf-8") as file:
                json.dump({"userdata": []}, file, ensure_ascii=False, indent=4)
                app_window = "App"

    # Starte immer den Flask-Server im Hintergrund
    threading.Thread(target=start_flask, daemon=True).start()

    if app_window == "App":
        # Starte Webview (blockierend!)
        webview.create_window("Dot Matrix Panel Client", "http://127.0.0.1:5000")
        webview.start()
    else:
        # App soll im Browser laufen – blockiere Hauptthread nicht sofort
        print("Starte Web-App im Browser")
        webbrowser.open("http://127.0.0.1:5000")

        # Hauptthread offenhalten, solange Server läuft
        while True:
            time.sleep(1)