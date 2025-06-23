#include <MD_MAX72xx.h>
#include <MD_Parola.h>
#include <WiFi.h>


#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
#define MAX_DEVICES 8
#define CLK_PIN 18
#define DATA_PIN 23
#define CS_PIN 5

#define PRINTS(x) Serial.print(F(x))

MD_MAX72XX mx = MD_MAX72XX(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);
MD_Parola P = MD_Parola(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);
#define DELAYTIME 100

int countX = 0;
int countY = 0;
int x = 0;
int y = 0;

int stateTimer = 1;

int current_millis;
int diff_millis;
int previous_millis;

int kommaIndex;

bool alert_state = 1;

String parts[2];


String input = "";
String lastInput = "";

String text = "Hallo Welt";

String nextMode = "";
String value = "";
//String input = "a";

String timerParts[3];

String clockParts[5];

String inputBuffer = "";

String transmissionMode = "WIFI";

const char* ssid = "Transfunk";
const char* password = "25JhJmXmssAnL12\\o/";

WiFiServer server(1234);  // Port wählen
WiFiClient client;
void setup() {
  bool serialModeDetected = false;
  unsigned long startTime;
  mx.begin();

  P.begin(3);          // 2 Zonen
  P.setZone(0, 0, 3);  // Zone 0 = Module 0 bis 7 (Panel A)
  P.setZone(1, 4, 7);
  P.setZone(2, 0, 7);

  //P.setIntensity(0, 2);  // Helligkeit Zone 0
  //P.setIntensity(1, 2);  // Helligkeit Zone 1
  P.displayClear();

  Serial.begin(9600);
    WiFi.begin(ssid, password);
      while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        //Serial.print(".");
      }
      //Serial.println("\nConnected via WIFI.");
      Serial.print("IP address:");
      Serial.println(WiFi.localIP());

      server.begin();
      //Serial.println("Waiting for connection...");
  
  }


void scrollText(char* p) {
  uint8_t charWidth;
  uint8_t cBuf[8];  // this should be ok for all built-in fonts
  PRINTS("\nScrolling text");
  mx.clear();
  while (*p != '\0') {
    charWidth = mx.getChar(*p++, sizeof(cBuf) / sizeof(cBuf[0]), cBuf);
    // allow space between characters
    for (uint8_t i = 0; i <= charWidth; i++) {
      mx.transform(MD_MAX72XX::TSL);
      if (i < charWidth) {
        mx.setColumn(0, cBuf[i]);
      }
      delay(DELAYTIME);
    }
  }
}

/*void coordinate() {
  mx.clear();
  int pixelX = x.toInt();
  int pixelY = y.toInt();
  mx.setPoint(pixelX, pixelY, true);
  delay(30);
}
*/
void print(String message) {
  mx.clear();
  P.print(message);
  delay(10);
}

void handleClientInput() {
  if (!client || !client.connected()) {
    client = server.available();
    if (client) {
      //Serial.println("Client verbunden.");
    }
  }
  if (client) {
    //Serial.println("Client verbunden.");
    if (client.connected()) {
      if (client.available()) {
        String msg = client.readStringUntil('\n');
        msg.trim();  // Leerzeichen und Zeilenumbrüche entfernen
        Serial.print("Empfangen: ");
        Serial.println(msg);
        input = msg;
        client.println("OK");  // Antwort zurückschicken
        client.flush();                // Warten, bis alles gesendet wurde
        //delay(100);
      }
    }
  }
}

void timer(String time) {
  int totalSeconds = 0;
  bool state = 1;
  if (time != "Break") {
    int firstSlash = time.indexOf('/');
    int secondSlash = time.indexOf('/', firstSlash + 1);

    if (firstSlash > 0 && secondSlash > firstSlash) {
      timerParts[0] = time.substring(0, firstSlash);
      timerParts[1] = time.substring(firstSlash + 1, secondSlash);
      timerParts[2] = time.substring(secondSlash + 1);
    }

    totalSeconds = timerParts[0].toInt() * 3600 + timerParts[1].toInt() * 60 + timerParts[2].toInt();

    unsigned long lastUpdate = millis();
    //P.setTextAlignment(1, PA_CENTER);
    //int state = 0;
    
    //while (client.connected()) {
    while (totalSeconds >= 0) {
      //Serial.println("In while");
      if (millis() - lastUpdate >= 1000) {
        lastUpdate = millis();
        //state = state + 1;
        int hours = totalSeconds / 3600;
        int minutes = (totalSeconds % 3600) / 60;
        int seconds = totalSeconds % 60;
        //mx.clear();
        char buffer[9];
        sprintf(buffer, "%02d:%02d", hours, minutes);
        //sprintf(buffer1, "%02d", seconds);

        P.displayClear();
        P.displayZoneText(1, buffer, PA_CENTER, 0, 0, PA_PRINT, PA_NO_EFFECT);

        char secondsOnly[3];
        sprintf(secondsOnly, "%02d", seconds);

        // Sekunden in Zone 0 anzeigen
        P.displayZoneText(0, secondsOnly, PA_CENTER, 0, 0, PA_PRINT, PA_NO_EFFECT);
        P.displayAnimate();

        totalSeconds--;

        handleClientInput();
        //Serial.println("Nach client if");
        if (input != "") {
          kommaIndex = input.indexOf(",");

          if (kommaIndex > 0) {
            parts[0] = input.substring(0, kommaIndex);   // vor dem Komma
            parts[1] = input.substring(kommaIndex + 1);  // nach dem Komma
          }
          nextMode = parts[0];
          value = parts[1];
          parts[0] = "";
          parts[1] = "";
          input = "";

          if (value != "Break") {
            state = 0;
            break;
          } else {
            state = 1;
          }
        }
      }
    }

  } else {
    totalSeconds = 0;
    state = 1;
  }
  P.displayClear();

  if (state == 1 || totalSeconds == 0) {
    alert();
    P.displayZoneText(1, "Timer", PA_CENTER, 0, 0, PA_PRINT, PA_NO_EFFECT);
    P.displayZoneText(0, "Ended", PA_CENTER, 0, 0, PA_PRINT, PA_NO_EFFECT);
    P.displayAnimate();
    delay(10);
    parts[0] = "";
    parts[1] = "";
    nextMode = "";
    value = "";
    input = "";
  }
}

void clock(String time) {
  Serial.print("Clock loop");
  String lastTime = "";
  String currentTime = time;
  bool x = 1;
  while (x) {
    int firstSlash = currentTime.indexOf('/');
    int secondSlash = currentTime.indexOf('/', firstSlash + 1);
    int thirdSlash = currentTime.indexOf("/", secondSlash + 1);
    int fourthSlash = currentTime.indexOf("/", thirdSlash + 1);

    if (firstSlash > 0 && secondSlash > firstSlash && thirdSlash > secondSlash && fourthSlash > thirdSlash) {
      clockParts[0] = currentTime.substring(0, firstSlash);                //Tag
      clockParts[1] = currentTime.substring(firstSlash + 1, secondSlash);  //Monat
      clockParts[2] = currentTime.substring(secondSlash + 1, thirdSlash);  //Jahr
      clockParts[3] = currentTime.substring(thirdSlash + 1, fourthSlash);  //Stunden
      clockParts[4] = currentTime.substring(fourthSlash + 1);              //Minuten
    }
    if (currentTime != lastTime) {
      char date[10];
      sprintf(date, "%02d.%02d.", clockParts[0].toInt(), clockParts[1].toInt());
      Serial.println(date);
      char time[10];
      sprintf(time, "%02d:%02d", clockParts[3].toInt(), clockParts[4].toInt());
      Serial.println(time);
      P.displayClear();
      //message = temperature + "C";
      
      P.displayZoneText(0, time, PA_CENTER, 0, 0, PA_PRINT, PA_NO_EFFECT);
      P.displayZoneText(1, date, PA_CENTER, 0, 0, PA_PRINT, PA_NO_EFFECT);
      P.displayAnimate();
      lastTime = currentTime;
    }

    //String input = Serial.readStringUntil('\n');
    handleClientInput();

    if (input != "") {
      kommaIndex = input.indexOf(",");

      if (kommaIndex > 0) {
        parts[0] = input.substring(0, kommaIndex);  // vor dem Komma
        parts[1] = input.substring(kommaIndex + 1);
      }
      if (parts[0] == "Clock") {
        currentTime = parts[1];
      } else {
        nextMode = parts[0];
        value = parts[1];
        x = 0;
        break;
      }
    }
  }
  parts[0] = "";
  parts[1] = "";
  input = "";
}

void weather(String temperature) {
  //float degrees = temperature.toFloat();
  //float roundedDegrees = round(degrees * 10) / 10.0;
  float degrees = temperature.toFloat();
  char message[10];
  sprintf(message, "%.1fC", degrees);  // z. B. "25.5C"
  Serial.print(message);
  P.displayClear();
  //message = temperature + "C";
  P.displayZoneText(1, message, PA_CENTER, 0, 0, PA_PRINT, PA_NO_EFFECT);
  P.displayAnimate();
  parts[0] = "";
  parts[1] = "";
  nextMode = "";
  value = "";
  input = "";
}

void leds_on() {
  for (uint8_t col = 0; col < MAX_DEVICES * 8; col++) {
    for (uint8_t row = 0; row < 8; row++) {
      mx.setPoint(row, col, true);  // (row, col, state)
    }
  }
}

void leds_off() {
  for (uint8_t col = 0; col < MAX_DEVICES * 8; col++) {
    for (uint8_t row = 0; row < 8; row++) {
      mx.setPoint(row, col, false);  // (row, col, state)
    }
  }
}

void alert() {
  int lastUpdate = 0;
  bool state = 1;
  int count = 0;
  while (alert_state) {
    if (millis() - lastUpdate >= 700) {
      lastUpdate = millis();
      if (state) {
        leds_on();
        state = 0;
      } else {
        leds_off();
        state = 1;
      }
      count = count + 1;
      if (count == 6) {
        state = 1;
        //alert_state = 0;
        break;
      }
    }
  }
}

void notes(String note) {
  alert();
  Serial.print("note: ");
  Serial.println(note);
  char note_text[100];
  sprintf(note_text, "%s", note.c_str());
  Serial.println(note_text);
  uint16_t cols = P.getTextColumns(note_text);
  Serial.print("Breite");
  Serial.println(cols);
  P.displayClear();

  P.displayZoneText(2, note_text, PA_LEFT, 0, 0, PA_PRINT, PA_NO_EFFECT);
  P.displayAnimate();
  parts[0] = "";
  parts[1] = "";
  nextMode = "";
  value = "";
}

void music(String title) {
  if (title == ""){
    Serial.println("Title empty");
  }
  char song_title[30];
  sprintf(song_title, "%s", title.c_str());
  Serial.print(song_title);
  P.displayClear();
  
  P.displayZoneText(2, song_title, PA_LEFT, 100, 0, PA_PRINT, PA_NO_EFFECT);
  P.displayAnimate();
  nextMode = "";
  value = "";
}

void loop() {
  //if (Serial.available())
  //String input = Serial.readStringUntil('\n');  // Lese bis Zeilenumbruch
  if (Serial.available()) {
    String request = Serial.readStringUntil('\n');
    if (request == "GET_IP") {
      Serial.println(WiFi.localIP());
    }
  }
  
  handleClientInput();
  //P.displayAnimate();
  if (input != ""){
  Serial.print("Input: ");
  Serial.println(input);
  }
  if (input != "") {
    kommaIndex = input.indexOf(",");

    if (kommaIndex > 0) {
      parts[0] = input.substring(0, kommaIndex);   // vor dem Komma
      parts[1] = input.substring(kommaIndex + 1);  // nach dem Komma
      nextMode = parts[0];
      value = parts[1];
    }
    input = "";
  }


  if (nextMode == "Timer") {
    nextMode = "";
    timer(value);
  }
  if (nextMode == "Spotify") {
    P.print("Spotify");
  }
  if (nextMode == "Clock") {
    clock(value);
  }
  if (nextMode == "Simhub") {
    P.print("Simhub");
  }
  if (nextMode == "Notes") {
    notes(value);
  }
  if (nextMode == "Weather") {
    weather(value);
  }
  if (nextMode == "Music") {
    music(value);
  }
  if (nextMode == "Break") {
    timer(value);
  }

  delay(10);

  //}
  //client.stop();
  //Serial.println("Client getrennt.");
  //}
}
