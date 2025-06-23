# Overview

This program is an application to display easily different things on a Dot-Matrix-Panel like the current weather or the actual playing songtitle. 
The two displays are controlled by an ESP (in my case ESP32, but it should also work with an ESP8266) which is connected via WIFI to a PC running this program to switch between different modes.
---
# Features
Possible things are possible to do with this tool:
- Display current weather
- Display current time and date
- Display current playing song on your PC (Windows only)
- Set and display a timer which send an optical reminder when it has expired
- Create a list from different tasks, every task send an optical reminder when it has expired

---
# Flash ESP
1. Clone this Git Repository to a folder of your choice
2. Extract the zip-file
3. Download the Arduino IDE from the official website (https://www.arduino.cc/en/software/) and install it
4. The ESP code is located in dot-matrix-info-display/Dot-Matrix_Panel/Dot-Matrix_Main_ESP/Dot-Matrix_Main_ESP.ino
5. Open this Dot-Matrix_Main_ESP.ino file by double click
6. The Arduino IDE is not able to work right out of the box together with an ESP. You have to change some settings in the IDE. Thats actually the most complicated part, but here are two good tutorials to set up the IDE: If you use an ESP32 use this tutorial: https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/. If you use an ESP8266 use this tutorial: https://randomnerdtutorials.com/how-to-install-esp8266-board-arduino-ide/
7. Once you set up the IDE you have to install some libraries via the library manager in the IDE (tutorial: https://docs.arduino.cc/software/ide-v2/tutorials/ide-v2-installing-a-library/)
8. Search for MD_MAX72xx and MD_Parola and install them
9. As the connection between your PC and the ESP will be via WIFI you have to enter the name of your WIFI network and the password of your WIFI network in the ESP Code. Simply replace the change me placeholders in line 53 and 54.
10. Everything is finished and you can flash the code on your ESP

---
# Installation of the python program 
1. Download the latest version of Python from the official python website (https://www.python.org/downloads/) and install it on your PC
2. Move in the cmd to the main/Dot-Matrix_Panel folder of this project, where the requirements.txt file is inside
3. Run the following command to install the necessary libraries:
  `pip install -r requirements.txt`
4. Move in the cmd to the main folder, where the Launcher.py file is inside
5. Run the following command:
  `python Launcher.py`
6. Everything is finished and you are ready to set up the program now

---
# Set up the program
1. Choose your username; you are able to change your username later
2. If you want to see the current temperature you have to enter an API key and your City, otherwise you leave both input fields empty and you can skip to point 3. I recommend to use a free API key from https://openweathermap.org
   3. Once you have created your account by https://openweathermap.org you are able to see and generate new API keys
   4. Copy one of the API keys and past them into the middle input field
   5. Search on the main page of https://openweathermap.org for your city. Once you have found it, copy the name of your city in the lowest input field, for example: Berlin, DE
6. Once you pressed Submit the program is waiting for a connection to the ESP. The program and the ESP communicate via WIFI, so it is necessary that the ESP and the PC running the program are in the same network
7. The program needs the ip address of the ESP to communicate with it. One you have connected the ESP via an USB-Kable to your PC press connect
8. If everything is working you should see a success page
9. You have to restart the program. You can disconnect the ESP from your computer and power it via a power supply of your choice.

---
# Tips and tricks
- The app window is actually a local hosted website displayed in an app window. The app windows is sometimes a little bit glitchy, that´s why you can choose to start the program in the browser in the settings page
- The `Launcher.py` file will automatically download the newest version of this program by the start of it 
- There is a dedicated page to view all running threads from the main program. You can reach it via the settings page