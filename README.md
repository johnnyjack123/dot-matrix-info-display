# Overview  
  
This program is an application for windows that allows you to easily display various types of information on a dot matrix panel,   
such as the current weather or the currently playing song title.  
It is designed to work with two 8 by 32 pixel displays.   
The two displays are controlled by an ESP (in my case, an ESP32, but it should also work with an ESP8266), which connects via Wi-Fi   to a PC running this program in order to switch between different display modes.  

---
# Features  
With this tool, you can:  
- Display the current weather  
- Display the current time and date  
- Display the currently playing song on your PC  
- Set and display a timer that sends a visual reminder when it expires  
- Create a task list where each task triggers a visual reminder when due  
  
---  
  
# Tutorial  
  
## Requirements  
1. **Dot Matrix Panel**  
    (I used two of these: [https://www.amazon.de/AZDelivery-MAX7219-Matrix-Anzeigemodul-Arduino/dp/B079HVW652/ref=sr_1_1](https://www.amazon.de/AZDelivery-MAX7219-Matrix-Anzeigemodul-Arduino/dp/B079HVW652/ref=sr_1_1))
    
2. **ESP Module**  
    (I used this one: [https://www.amazon.de/diymore-Nodemcu-Development-Bluetooth-2-ESP32/dp/B0D9BTQRYT/ref=sr_1_10](https://www.amazon.de/diymore-Nodemcu-Development-Bluetooth-2-ESP32/dp/B0D9BTQRYT/ref=sr_1_10))
    
3. **Case for the displays and ESP**  
    I designed a custom case that fits both the displays and the ESP.
    
    1. You can view the case here: [CAD model on Onshape](https://cad.onshape.com/documents/d29c9376a775a0af4be5ebed/w/a185d0d36c678531ea7d5ad4/e/14183a4fe48a4bc153d143a9?renderMode=0&uiState=685e853326e607746c0e7225)
        
    2. The `.stl` file is included in the main folder of this project (`Dot-Matrix-Display_Case.stl`)
        
4. **Important Note**  
    The ESP only fits inside the case if you solder the display wires directly to the ESP. Using pin headers will not work due to space constraints.
  
---  
## Flash the ESP

1. Clone this Git repository to a folder of your choice.
    
2. Extract the ZIP file.
    
3. Download and install the Arduino IDE from the official website: [https://www.arduino.cc/en/software/](https://www.arduino.cc/en/software/)
    
4. The ESP code is located in:  
    `dot-matrix-info-display-master/Dot-Matrix_Panel/Dot-Matrix_Main_ESP/Dot-Matrix_Main_ESP.ino`
    
5. Open the `Dot-Matrix_Main_ESP.ino` file by double-clicking it.
    
6. The Arduino IDE does not work with an ESP right out of the box. You’ll need to change some settings first. This is probably the most complicated part, but here are two good setup guides:
    - For ESP32: [ESP32 setup tutorial](https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/)
    - For ESP8266: [ESP8266 setup tutorial](https://randomnerdtutorials.com/how-to-install-esp8266-board-arduino-ide/)
        
7. Once the IDE is set up, open the Library Manager and install the following libraries:
    - `MD_MAX72xx`
    - `MD_Parola`  
    - You can find a detailed library installation guide here:  [Library installation tutorial](https://docs.arduino.cc/software/ide-v2/tutorials/ide-v2-installing-a-library/)
        
8. Since the ESP connects to your PC via Wi-Fi, you’ll need to enter your Wi-Fi name (SSID) and password in the ESP code. Replace the placeholder values in lines 53 and 54 in the Dot-Matrix_Main_ESP.ino file. The file is located in /dot-matrix-info-display-master/Dot-Matrix_Panel/Dot-Matrix_Main_ESP/Dot-Matrix_Main_ESP.ino
    
9. Once that’s done, you can flash the code onto your ESP.
  
---  
## Install the Python Program

1. Download and install the latest version of Python from the official website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    
2.  Locate the file `launcher.bat` in the `dot-matrix-info-display-master` folder and open it by double-clicking it.
    
3. A warning window may pop up. You need to allow Windows to execute the script. If you don’t want to allow it, you can also open the file in a text editor and manually copy the commands into your command line.
4. If you want to use a cool pixel-style font, install the font located at dot-matrix-info-display/Dot-Matrix_Panel/templates/5by7.ttf by double-clicking the file.
5. The script will automatically set up and activate a virtual environment and install all necessary libraries. After that, the program will start. I recommend always launching the program via the `launcher.bat` file, as it’s the easiest and most reliable way to start it.
  
---  
## Set up the program  

1. Choose a username — you can change it later if needed.
    
2. If you want to display the current temperature, you need to enter an API key and your city. Otherwise, leave the input fields empty and skip to step 3.
    
    - I recommend using a free API key from [https://openweathermap.org](https://openweathermap.org)
        
    - After creating an account, go to your dashboard to view and generate API keys.
        
    - Copy one of your API keys and paste it into the middle input field.
        
    - Search for your city on the OpenWeatherMap homepage. Once found, copy the city name (e.g. `Berlin, DE`) into the bottom input field.
        
3.  Click "Submit". The program will now wait for a connection to the ESP. Make sure both the ESP and your PC are connected to the same Wi-Fi network.
    
4. The program needs the ESP's IP address to communicate. While the ESP is connected to your PC via USB, press "Connect".
    
5.  If everything works, a success message should appear.
    
6.  You can now restart the program. The ESP can be disconnected from your PC and powered by any external power supply.
  
---  
## Tips and tricks  
- The app window is actually a locally hosted website displayed in an app shell. Sometimes the app window might behave a bit glitchy, so you can choose to open it in your browser via the settings page.
    
- The `Launcher.py` script will automatically check for and download the latest version of the program when it starts.
    
- There is a dedicated page for viewing all running threads of the main program — accessible from the settings page.