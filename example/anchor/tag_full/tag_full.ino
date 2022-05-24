#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_HMC5883_U.h>

#include <SPI.h>
#include "DW1000Ranging.h"
#include <WiFi.h>
#include "link.h"

#define SPI_SCK 18
#define SPI_MISO 19
#define SPI_MOSI 23
#define DW_CS 4

// connection pins
const uint8_t PIN_RST = 27; // reset pin
const uint8_t PIN_IRQ = 34; // irq pin
const uint8_t PIN_SS = 4;   // spi select pin

const char *ssid = "MarVova";
const char *password = "PASSWORD";
const char *host = "192.168.1.106";
WiFiClient client;

struct MyLink *uwb_data;
int index_num = 0;
long runtime = 0;
String all_json = "";

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels

// Declaration for an SSD1306 display connected to I2C (SDA, SCL pins)
// The pins for I2C are defined by the Wire-library.
// On an arduino UNO:       A4(SDA), A5(SCL)
// On an arduino MEGA 2560: 20(SDA), 21(SCL)
// On an arduino LEONARDO:   2(SDA),  3(SCL), ...
#define OLED_RESET 4        // Reset pin # (or -1 if sharing Arduino reset pin)
#define SCREEN_ADDRESS 0x3C ///< See datasheet for Address; 0x3D for 128x64, 0x3C for 128x32
TwoWire I2C1 = TwoWire(0);  // I2C1 bus
/* Assign a unique ID to this sensor at the same time */
Adafruit_HMC5883_Unified mag = Adafruit_HMC5883_Unified(12345, &I2C1);

unsigned long lastScreenUpdate = 0;


float xMax, yMax, xMin, yMin = 0.0;

void displaySensorDetails(void)
{
  sensor_t sensor;
  mag.getSensor(&sensor);
  Serial.println("------------------------------------");
  Serial.print("Sensor:       ");
  Serial.println(sensor.name);
  Serial.print("Driver Ver:   ");
  Serial.println(sensor.version);
  Serial.print("Unique ID:    ");
  Serial.println(sensor.sensor_id);
  Serial.print("Max Value:    ");
  Serial.print(sensor.max_value);
  Serial.println(" uT");
  Serial.print("Min Value:    ");
  Serial.print(sensor.min_value);
  Serial.println(" uT");
  Serial.print("Resolution:   ");
  Serial.print(sensor.resolution);
  Serial.println(" uT");
  Serial.println("------------------------------------");
  Serial.println("");
  delay(500);
}

void setupUWB()
{
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected");
  Serial.print("IP Address:");
  Serial.println(WiFi.localIP());

  if (client.connect(host, 4545))
  {
    Serial.println("Success");
    client.print(String("GET /") + " HTTP/1.1\r\n" +
                 "Host: " + host + "\r\n" +
                 "Connection: close\r\n" +
                 "\r\n");
  }

  delay(1000);

  // init the configuration
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  DW1000Ranging.initCommunication(PIN_RST, DW_CS, PIN_IRQ);
  DW1000Ranging.attachNewRange(newRange);
  DW1000Ranging.attachNewDevice(newDevice);
  DW1000Ranging.attachInactiveDevice(inactiveDevice);

  // we start the module as a tag
  DW1000Ranging.startAsTag("7D:00:22:EA:82:60:3B:9C", DW1000.MODE_LONGDATA_RANGE_LOWPOWER);

  uwb_data = init_link();
}

void setup(void)
{
  Serial.begin(9600);
  setupUWB();

#if 1
  I2C1.begin(27,26);
  Serial.println("MARINKA");
  Serial.println("");

  /* Initialise the sensor */
  if (!mag.begin())
  {
    /* There was a problem detecting the HMC5883 ... check your connections */
    while (1)
    {
      Serial.println("Ooops, no HMC5883 detected ... Check your wiring!");
      delay(1000);
    }
  }

  displaySensorDetails();


 #endif
}

float headingDegrees = 0;
unsigned long startTime = 0;
bool calibrated = false;
void loop(void)
{
  if (startTime == 0) {
    startTime = millis();
  }
  unsigned long now = millis();


  #if 1
  if ((now - lastScreenUpdate) > 250)
  {
    Serial.println("Reading sensor data...");
    /* Get a new sensor event */
    sensors_event_t event;
    mag.getEvent(&event);

    bool calibrate = (now - startTime) < 30000;
    calibrated = !calibrate;
    if (xMax == 0.0) {
      xMax = event.magnetic.x;
    }
  
    if (yMax == 0.0) {
      yMax = event.magnetic.y;
    }
  
    if (calibrate) {
      xMax = max(xMax, event.magnetic.x);
      yMax = max(yMax, event.magnetic.y);
      xMin = min(xMin, event.magnetic.x);
      yMin = min(yMin, event.magnetic.y);
    }

    /* Display the results (magnetic vector values are in micro-Tesla (uT)) */
    /*Serial.print("X: ");
    Serial.print(event.magnetic.x);
    Serial.print("  ");
    Serial.print("Y: ");
    Serial.print(event.magnetic.y);
    Serial.print("  ");
    Serial.print("Z: ");
    Serial.print(event.magnetic.z);
    Serial.print("  ");
    Serial.println("uT");*/
    if (calibrated) {
      float heading = atan2((event.magnetic.y - ((yMax + yMin) / 2.0)), (event.magnetic.x - ((xMax + xMin) / 2.0)));

      // Once you have your heading, you must then add your 'Declination Angle', which is the 'Error' of the magnetic field in your location.
      // Find yours here: http://www.magnetic-declination.com/
      // Mine is: -13* 2' W, which is ~13 Degrees, or (which we need) 0.22 radians
      // If you cannot find your Declination, comment out these two lines, your compass will be slightly off.
      float declinationAngle = 0.22;
      heading += declinationAngle;
  
      // Correct for when signs are reversed.
      if (heading < 0)
        heading += 2 * PI;
  
      // Check for wrap due to addition of declination.
      if (heading > 2 * PI)
        heading -= 2 * PI;
  
      // Convert radians to degrees for readability.
      headingDegrees = heading * 180 / M_PI;
  
      int radius = 15;
  
      Serial.print("Heading (degrees): ");
      Serial.println(headingDegrees);
    }
    lastScreenUpdate = now;
  }
  #endif
  DW1000Ranging.loop();
  if ( (millis() - runtime) > 1000 && calibrated)
  {
    make_link_json(uwb_data, &all_json, headingDegrees);
    send_udp(&all_json);
    runtime = millis();
  }
}

void newRange()
{
  char c[30];

  Serial.print("from: ");
  Serial.print(DW1000Ranging.getDistantDevice()->getShortAddress(), HEX);
  Serial.print("\t Range: ");
  Serial.print(DW1000Ranging.getDistantDevice()->getRange());
  Serial.print(" m");
  Serial.print("\t RX power: ");
  Serial.print(DW1000Ranging.getDistantDevice()->getRXPower());
  Serial.println(" dBm");
  fresh_link(uwb_data, DW1000Ranging.getDistantDevice()->getShortAddress(), DW1000Ranging.getDistantDevice()->getRange(), DW1000Ranging.getDistantDevice()->getRXPower());
}

void newDevice(DW1000Device *device)
{
  Serial.print("ranging init; 1 device added ! -> ");
  Serial.print(" short:");
  Serial.println(device->getShortAddress(), HEX);

  add_link(uwb_data, device->getShortAddress());
}

void inactiveDevice(DW1000Device *device)
{
  Serial.print("delete inactive device: ");
  Serial.println(device->getShortAddress(), HEX);

  delete_link(uwb_data, device->getShortAddress());
}

void send_udp(String *msg_json)
{
  if (client.connected())
  {
    client.print(*msg_json);
    Serial.println("UDP send");
  } else {
    client.connect(host, 4545);
  }
}
