from datetime import datetime
import time

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import webview
import threading
import requests
import json
import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
import webbrowser
from Dot_Matrix_Panel.outsourced_functions import read, save, get_secret_key
from Dot_Matrix_Panel.wifi_connection import collect_messages, start_send
from Dot_Matrix_Panel.serial_connection import start_get_port
from Dot_Matrix_Panel.python_serial_debug_window import start_serial_monitor_server
from Dot_Matrix_Panel.logger import logger
import Dot_Matrix_Panel.global_variables as global_variables

secret_key = get_secret_key()

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
from Dot_Matrix_Panel import sockets
sockets.init_socket(socketio)
from Dot_Matrix_Panel.sockets import send_socket

@app.route('/')
def index():
    stop_clock()
    stop_weather()
    stop_music()
    file = read()
    if file["userdata"]["username"]:
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

last_song = ""

title = ""
current_title = ""

running_threads = []
sleeping_threads = []

#esp_ip = ""
#port = 1234

connection = True #State variable to check if esp is connected or not

actual_screen = global_variables.screen

debug = True

@app.route('/initial_connect', methods=["GET"])
def initial_connect():
    #send_socket("status_message", "Loading")
    return render_template("success.html")

@app.route('/connect', methods=["POST", "GET"])
def connect():
    data = read()
    esp_data = data["esp_data"]

    if not esp_data["ip"]:
        connection_state = True
        logger.info("No ESP ip available.")
    else:
        connection_state = False

    return render_template("connect.html", connection_state=connection_state)


@app.route('/dashboard')
def dashboard():
    stop_clock()
    stop_weather()
    stop_music()
    file = read()
    userdata = file["userdata"]
    username = userdata["username"]
    if username:
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
    #print("Title: " + title)
    return render_template('music.html', title=title)

@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    global note, remind_time, task_thread, task_collection
    if request.method == 'POST':
        if request.method == 'POST':
            if 'delete' in request.form:
                delete_time = request.form['delete']
                task_collection.pop(delete_time, None)
                #print(task_collection)
            else:
                note = request.form['task']
                remind_time = str(request.form['remind_time'])
                if remind_time in task_collection:
                    return render_template('internal_server_error.html', error="Its not possible to create two tasks with the same time")
                task_collection[remind_time] = note
                task_thread = False
                #print(type(remind_time), remind_time)
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
    global rounded_temperature
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
    file = read()

    username = request.form["username"]
    weather_api_key = request.form.get("weather_api_key")
    city = request.form.get("city")

    ssid = request.form.get("ssid")
    password = request.form.get("password").replace("\\", "\\")

    if not username or not ssid or not password:
        return render_template("landing.html")

    userdata = file["userdata"]
    esp_data = file["esp_data"]

    userdata["username"] = username
    userdata["weather_api_key"] = weather_api_key
    userdata["city"] = city

    esp_data["ssid"] = ssid
    esp_data["password"] = password

    file["userdata"] = userdata
    file["esp_data"] = esp_data
    save(file)
    logger.info("User created.")
    return render_template("connect.html", connection_state = True)

@app.route('/manage_threads', methods=["POST", "GET"])
def manage_threads():
    global weather_thread_started, timer_thread, task_thread, send_thread, monitoring_thread, running_threads, sleeping_threads

    return render_template("thread_monitoring.html", running_threads=running_threads, sleeping_threads=sleeping_threads)

@app.route('/settings_page', methods=["POST", "GET"])
def settings_page():
    with open("Dot_Matrix_Panel/version.txt", "r", encoding="utf-8") as file:
        version = "Version: " + str(file.read().strip())

        data = read()

        user = data["userdata"]
        app_window = user["open"]
        if app_window == "App":
            switch_state = True
        else:
            switch_state = False

        return render_template("settings.html", version=version, switch_state=switch_state)

@app.route('/settings', methods=["POST", "GET"])
def settings():
    switch_state = True

    if request.method == "POST":
        username = request.form.get("username")
        esp_ip = request.form.get("ip")
        api_key = request.form.get("weather_api_key")
        city = request.form.get("city")
        switch = request.form.get("switch")

        file = read()


        user = file["userdata"]

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

        file["userdata"] = user
        save(file)
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
                    if not global_variables.screen == "Timer":
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
            for task_time, task in list(task_collection.items()):
                current_time = f"{now[3]:02}:{now[4]:02}"
                if task_time == current_time:
                    time.sleep(0.2)
                    message = "Notes," + task
                    collect_messages(message)
                    del task_collection[task_time]
                    time.sleep(1)

                    if not len(task_collection) > 0:
                        stop_tasks()
                        stop_music()
                        stop_weather()
                        stop_clock()
                        return
                time.sleep(1)
        time.sleep(1)

# Background function to get the time
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
    file = read()
    if file["userdata"]:
        userdata = file["userdata"]
        API_KEY = userdata["weather_api_key"]
        stadt = userdata["city"]
        url = f"http://api.openweathermap.org/data/2.5/weather?q={stadt}&appid={API_KEY}&units=metric&lang=de"

        while weather_thread_started:
            global now
            if now[4] != last_minute:
                count = count + 1
                last_minute = now[4]
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
                        else:
                            logger.error("Unable to get weather datas")
                            rounded_temperature = "Weather unavailable. Please check your API key."
                    except Exception as e:
                        logger.error(f"Error in weather: {e}")
            else:
                time.sleep(1)

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
            last_song = str(title)
        time.sleep(1)
    else:
        logger.info("No active media session found.")

def send_music(song):
    global current_title
    if title != "":
        if title != current_title:
            collect_messages("Music," + title)
            current_title = title

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

def start_flask():
    global debug
    socketio.run(app, debug=debug, use_reloader=False, allow_unsafe_werkzeug=True)
    logger.info("Server started")

# Start
if __name__ == '__main__':
    file = read()
    userdata = file["userdata"]
    if debug:
        start_serial_monitor_server()
    start_get_port()
    start_send()
    start_get_time()
    # Starte immer den Flask-Server im Hintergrund
    threading.Thread(target=start_flask, daemon=True).start()

    if userdata["open"] == "App":
        webview.create_window("Dot Matrix Panel Client", "http://127.0.0.1:5000")
        webview.start()
    else:
        webbrowser.open("http://127.0.0.1:5000")

        # Hauptthread offenhalten, solange Server läuft
        while True:
            time.sleep(1)

# TODO: Clock zeigt auf Display immer 0