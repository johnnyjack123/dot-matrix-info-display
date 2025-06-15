import serial
from datetime import datetime
import time

#from Demos.win32ts_logoff_disconnected import username
from eventlet.websocket import utf8validator
from flask import Flask, render_template, request, redirect, url_for, jsonify
import webview
import threading
import requests
import json
from pycparser.c_ast import While
import socket
import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
import serial.tools.list_ports
import unidecode


API_KEY = "f16048e6b70dfde733c42b2d26f7e0e1"  # ← hier deinen API-Key einfügen
stadt = "Dresden"
url = f"http://api.openweathermap.org/data/2.5/weather?q={stadt}&appid={API_KEY}&units=metric&lang=de"

app = Flask(__name__)

arduino_port = 'COM6'
baud_rate = 9600
#ser = serial.Serial(arduino_port, baud_rate, timeout=1)

running_clock = False
clock_thread = None

music_thread_started = False
weather_thread_started = False
timer_thread = False
notes_thread = False
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
note_collection = {}

messages = []

json_structure = {"userdata": []}

last_song = ""

transmission_method = ""

title = ""

@app.route('/')
def index():
    stop_clock()
    stop_weather()
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        if data.get("userdata") and any("username" in user for user in data["userdata"]):
            userdata = data.get("userdata", [])
            username = userdata[-1]["username"]
            return render_template('index.html', username=username)
        else:
            return render_template("landing.html")


@app.route('/clock')
def clock():
    global now
    start_clock()
    stop_weather()
    return render_template('clock.html', year=now[0], month=now[1], day=now[2], hour=now[3], minute=now[4])

@app.route('/stop_clock')
def stop_clock_route():
    stop_clock()
    return redirect(url_for('index'))

@app.route('/api/time')
def api_time():
    global now
    #now = datetime.now()
    return jsonify({
        'day': now[2],
        'month': now[1],
        'year': now[0],
        'hour': f"{now[3]:02}",
        'minute': f"{now[4]:02}"
    })

@app.route('/timer', methods=['GET', 'POST'])
def timer_page():
    global hours, minutes, seconds
    stop_clock()
    stop_weather()
    if not state_timer:
        if request.method == 'POST':
            hours = request.form['hours']
            minutes = request.form['minutes']
            seconds = request.form['seconds']
            timer_time = hours + "/" + minutes + "/" + seconds
            message = f"Timer,{timer_time}"
            #ser.write(message.encode('utf-8'))
            collect_messages(message)
            start_timer()
            return render_template('timer.html', sent_time=timer_time)
    else:
        timer_time = str(hours) + "/" + str(minutes) + "/" + str(seconds)
        message = f"Timer,{timer_time}"
        #ser.write(message.encode('utf-8'))
        collect_messages(message)
    return render_template('timer.html', sent_time=None)

@app.route('/music')
def music():
    global title
    stop_clock()
    stop_weather()
    #asyncio.run(get_song_info())
    start_music()
    time.sleep(0.2)
    return render_template('music.html', title=title)

@app.route('/notes', methods=['GET', 'POST'])
def display_notes():
    global note, remind_time, notes_thread, note_collection
    stop_clock()
    stop_weather()
    if request.method == 'POST':
        if request.method == 'POST':
            if 'delete' in request.form:
                delete_time = request.form['delete']
                note_collection.pop(delete_time, None)
                print(note_collection)
            else:
                note = request.form['task']
                remind_time = str(request.form['remind_time'])
                if remind_time in note_collection:
                    return render_template('internal_server_error.html', error="Its not possible to create two tasks with the same time")
                note_collection[remind_time] = note
                notes_thread = False
                print(type(remind_time), remind_time)
                start_notes()
    return render_template('notes.html', tasks=note_collection)

@app.route('/simhub')
def simhub():
    stop_clock()
    stop_weather()
    return render_template('simhub.html')

@app.route('/weather')
def weather():
    stop_clock()
    start_weather()
    time.sleep(0.4)
    return render_template('weather.html', temperature=rounded_temperature)

@app.route('/api/temperature')
def api_temperature():
    return jsonify({
        'temperature': str(rounded_temperature) + "°C"
    })

@app.route('/api/notes')
def api_notes():
    return jsonify(note_collection)

@app.route('/api/music')
def api_music():
    global title
    return jsonify({"title": title})

@app.route('/landing', methods=['GET', 'POST'])
def landing():
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Stelle sicher, dass "userdata" existiert
    if "userdata" not in data:
        data["userdata"] = []

    # Füge neuen Eintrag hinzu
    new_entry = {
        "username": request.form["username"],
        "ip": request.form["ip"],
    }
    data["userdata"].append(new_entry)

    # Speichern
    with open("userdata.json", "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    # Weiterleitung basierend auf Erfolg
    if data.get("userdata") and any("username" in user for user in data["userdata"]):
        return render_template("index.html", username=request.form["username"])
    else:
        return render_template("landing.html")

@app.route('/manage_threads')
def manage_threads:
    global weather_thread_started, timer_thread, notes_thread, send_thread, monitoring_thread
    start_thread_monitoring()
    time.sleep(0.2)
    running_threads = []
    sleeping_threads = []
    threads = [{ "name": "weather_thread_started", "value": weather_thread_started }, {"name": "timer_thread", "value": timer_thread}, {"name": "notes_thread", "value": notes_thread}, {"name": "send_thread", "value": send_thread}, {"name": "monitoring_thread", "value": monitoring_thread}]
    for thread in threads:
        if thread.value:
            running_threads.append(thread.name)
        else:
            sleeping_threads.append(thread.name)

    return render_template("thread_monitoring.html", running_threads, sleeping_threads)

def start_timer():
    global timer_thread
    if not timer_thread:
        time.sleep(1.5)
        thread = threading.Thread(target=timer, daemon=True)
        thread.start()

def stop_timer():
    global timer_thread
    timer_thread = False

def timer():
    global hours, minutes, seconds, state_timer
    while True:
        state_timer = True
        #print("Timer is running")
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
                    state_timer = False
                    break
                else:
                    minutes = 59
                    hours = int(hours) - 1

def start_notes():
    global notes_thread
    if not notes_thread:
        notes_thread = True
        thread = threading.Thread(target=notes, daemon=True)
        thread.start()

def stop_notes():
    global notes_thread
    notes_thread = False

def notes():
    global now, notes_thread, note_collection
    while True:
        if len(note_collection) > 0:
            # Über eine KOPIE des Dictionaries iterieren:
            for task_time, task in list(note_collection.items()):
                current_time = f"{now[3]:02}:{now[4]:02}"
                if task_time == current_time:
                    time.sleep(0.2)
                    #ascii_message = unidecode.unidecode(task)
                    ascii_message = calculate_messsage_length(task)
                    message = "Notes," + ascii_message
                    collect_messages(message)
                    print(message)
                    print("Note sent")
                    print(note_collection)
                    del note_collection[task_time]  # Sicheres Löschen
                    time.sleep(1)
                    #TODO Thread beenden

                    if not len(note_collection) > 0:
                        notes_thread = True
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

        #print("Clock is running")
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
    while weather_thread_started:
        global now
        #now = datetime.now()
        #minute = now.minute
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
                        #ser.write(message.encode('utf-8'))
                        #send(message)
                        collect_messages(message)
                        count = 0
                        print("New temperature set")
                    else:
                        print("Unable to get weather datas")
                except Exception as e:
                    print("Unable to send message")
        else:
            time.sleep(1)
    print("Weather stopped")

# Hintergrundfunktion: Jede Minute Uhrzeit senden
def clock_loop():
    global now
    last_minute = -1
    global running_clock
    while running_clock:
        #now = datetime.now()
        if now[4] != last_minute:
            message = f"Clock,{now[2]}/{now[1]}/{now[0]}/{now[3]}/{now[4]}"
            #send(message)
            #ser.write(message.encode('utf-8'))
            collect_messages(message)
            #print("Gesendet:", message)
            last_minute = now[4]
            #clock()
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

def get_music():
    while True:
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
            message = str(title)
            ascii_message = unidecode.unidecode(message)
            ascii_message = calculate_messsage_length(ascii_message)
            collect_messages("Music," + ascii_message)

            print(f"Title: {title}")
            print(f"Artist: {artist}")
            print(f"Album: {album}")
            last_song = str(title)
        time.sleep(1)
    else:
        print("No active media session found.")

# Run the async function


def start_send():
    global send_thread
    if not send_thread:
        send_thread = True
        thread = threading.Thread(target=send, daemon=True)
        thread.start()

def collect_messages(value: str):
    global messages
    messages.append(value)

def send():
    global messages
    with open("userdata.json", "r", encoding="utf-8") as file:
        data = json.load(file)
        userdata = data["userdata"]

        if userdata:  # Sicherstellen, dass die Liste nicht leer ist
            esp_ip = userdata[-1]["ip"]  # letzter gespeicherter IP-Eintrag
            print("ESP IP:", esp_ip)
        else:
            print("No userdata available")
    port = 1234
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((esp_ip, port))
        print("Connected with ESP")
        while True:
            #print("Send is running")
            time.sleep(0.1)
            if len(messages) != 0:
                messages.reverse()
                message: str = str(messages.pop())
                messages.reverse()

                #ascii_message = unidecode.unidecode(message)
                #message = calculate_messsage_length(message)
                s.sendall(message.encode("utf-8"))
                data = b""
                while not data.endswith(b'\n'):
                    part = s.recv(1024)
                    if not part:
                        break
                    data += part

                print("Answer from ESP:", data.decode("utf-8").strip())
                time.sleep(2) #TODO erst wenn Signal von ESP kommt, weiter machen

def calculate_messsage_length(ascii_message):
    text_size = len(ascii_message) * 5 #approximately 5 pixels per letter
    if text_size > 55:
        new_text = ascii_message[:10] + "."
        ascii_message = new_text
        return ascii_message
    return ascii_message

def start_thread_monitoring():
    global monitoring_thread
    if not monitoring_thread:
        monitoring_thread = True
        thread = threading.Thread(target=thread_monitoring, daemon=True)
        thread.start()

def thread_monitoring():
    global weather_thread_started, timer_thread, notes_thread, send_thread, monitoring_thread
    while True:
        if weather_thread_started:
            print("Weather is running")
        if timer_thread:
            print("Timer is running")
        if notes_thread:
            print("Note is running")
        if send_thread:
            print("Send is running")
        if monitoring_thread:
            print("Monitoring is running")
        print("---\n")
        time.sleep(10)

def start_flask():
    app.run()


start_get_time()
start_send()
start_thread_monitoring()

# Start
if __name__ == '__main__':
    threading.Thread(target=start_flask, daemon=True).start()
    webview.create_window("Arduino Zeitsteuerung", "http://127.0.0.1:5000")
    webview.start()
    #start_thread_monitoring()

