import time
from datetime import datetime
import sys,os
from pathlib import Path
import threading
from threading import Event, Thread
import configparser
import socket
from subprocess import check_output

import Adafruit_DHT
import lcddriver
import RPi.GPIO as GPIO     #sudo apt-get install rpi.gpio
from  ValueHistory import *

import paho.mqtt.client as mqtt 

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
BUTTON_PIN = 21

UPDATE_INTERVAL = 10
HISTORY_LEN = 12

MODE_FIRST = 1
MODE_CLOCK = 1
MODE_TEMPHUMID = 2
MODE_MINMAX_TEMP = 3
MODE_STATS = 4
MODE_LAST = 4

current_mode = MODE_CLOCK
button_start = None
BUTTON_LONG_PRESS = 3

DISPLAY_LOCK = threading.Lock()
DATA_LOCK = threading.Lock()

# Read configuration from external file
# https://docs.python.org/2/library/configparser.html#examples
CONFIG = configparser.ConfigParser()

SCRIPT_DIR = (os.path.dirname(os.path.realpath(__file__))) + "/"
CONFIG_FILE_NAME = SCRIPT_DIR + Path(__file__).stem + ".ini"
try:
    CONFIG.read(CONFIG_FILE_NAME)
except Exception as e :
    print(str(e))

val = CONFIG.get('display', 'attached')
if val is not None:
    DISPLAY_ATTACHED = (val == "True")
else:
    DISPLAY_ATTACHED = False
if not DISPLAY_ATTACHED:
    print("Running headless. No display attached.")

val = CONFIG.get('dht22', 'pin')
if val is not None:
    DHT_PIN = int(val)

val = CONFIG.get('button', 'pin')
if val is not None:
    BUTTON_PIN = int(val)

MQTT_ENABLED = False
val = CONFIG.get('mqtt', 'enabled')
if val is not None:
    MQTT_ENABLED = bool(val)

if MQTT_ENABLED:
    print("MQTT reporting has been enabled in the settings .ini file")
else:
    print("MQTT reporting has been disabled in the settings .ini file")

MQTT_SERVER = CONFIG.get('mqtt', 'server')
MQTT_PORT = int(CONFIG.get('mqtt', 'port'))
MQTT_ROOT_TOPIC =CONFIG.get('mqtt', 'roottopic')
MQTT_USER = CONFIG.get('mqtt', 'user')
MQTT_PASS = CONFIG.get('mqtt', 'pass')

mqtt_client = None

class RaspiCPU:
    def __init__(self):
        self.cpu_temp = None
        self.ip_address = None

    def temp(self):
        output = str(check_output(['vcgencmd', 'measure_temp']))        
        t = output[output.index('=') + 1:output.rindex("'")]
        self.cpu_temp = float(t)
        return self.cpu_temp

    def ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.ip_address = s.getsockname()[0]
        return self.ip_address

def setupButton(pin):
    if pin <= 0:
        return
    GPIO.setwarnings(True)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin,GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(pin,GPIO.FALLING,callback=OnButtonPress,bouncetime=2000) 

# Invoked when the button is initially pressed
def OnButtonPress(channel):
    global button_start
    button_start = time.time()
    GPIO.remove_event_detect(channel)        
    GPIO.add_event_detect(channel, GPIO.RISING, callback=OnButtonRelease, bouncetime=2000)

# Invoked when the button is released
def OnButtonRelease(channel):
    global button_start, BUTTON_LONG_PRESS

    button_duration = time.time() - button_start

    GPIO.remove_event_detect(channel)
    GPIO.add_event_detect(channel, GPIO.FALLING, callback=OnButtonPress, bouncetime=2000)

    # Short Press = Restart, Long Press = Shutdown
    if button_duration < BUTTON_LONG_PRESS:
        OnButtonShortPress(channel)
    else:
        OnButtonLongPress(channel)
    UpdateDisplay()

def OnButtonShortPress(channel):
    global current_mode
    current_mode += 1
    if current_mode > MODE_LAST:
        current_mode = MODE_FIRST
    print("Short Press: Change Display Mode")

def OnButtonLongPress(channel):
    global current_mode, temp_history, humid_history
    print("Long press: Resetting values")
    with DATA_LOCK:
        temp_history = None
        humid_history = None 

def UpdateDisplay():
    global current_mode, display, temp_history, humid_history, rpi
    with DATA_LOCK:
        if temp_history is None or humid_history is None:
            print("History values have been reset.")
        else:
            print(str(temp_history) + "\t" + str(humid_history))
        if DISPLAY_ATTACHED:
            with DISPLAY_LOCK:
                display.lcd_clear()
                if current_mode == MODE_TEMPHUMID: 
                    display.lcd_display_string("Temp(F) Humid(%)",1)
                    if temp_history is None or humid_history is None:
                        display.lcd_display_string(" ..resetting.. ",2)
                    else:
                        display.lcd_display_string("{0:0.1f}{1}      {2:0.1f}{3}".format(temp_history.current.value,temp_history.trend, humid_history.current.value, humid_history.trend),2)
                elif current_mode == MODE_MINMAX_TEMP:
                    if temp_history is None:
                        display.lcd_display_string("Min Temp:    n/a",1)
                        display.lcd_display_string("Max Temp:    n/a",2)
                    else:
                        display.lcd_display_string("Min Temp:  {0:0.1f}F".format(temp_history.min),1)
                        display.lcd_display_string("Max Temp:  {0:0.1f}F".format(temp_history.max),2)
                elif current_mode == MODE_CLOCK:
                    current = datetime.now()
                    display.lcd_display_string(current.strftime("%a %b-%d-%Y"),1)
                    display.lcd_display_string(current.strftime("%-I:%M%P").lstrip("0").replace(" 0", " ") + "   {0:0.1f}F{1}".format(temp_history.current.value,temp_history.trend),2)
                elif current_mode == MODE_STATS:
                    cpu_temp = 9.0/5.0 * rpi.temp() + 32
                    display.lcd_display_string("{0:.1f}F".format(cpu_temp),1)
                    display.lcd_display_string(rpi.ip(),2)
                else:
                    display.lcd_display_string("Unknown Mode",1)

def OnSettingsUpdated(settings):
    global UPDATE_INTERVAL
    try:
        if settings is not None:
            if "SensorFrequency" in settings.keys():
                freq = settings["SensorFrequency"]
                if freq is not None:
                    UPDATE_INTERVAL = freq
                    print("Update Interval: {0:.2f}".format(UPDATE_INTERVAL))
            else:
                print("Missing SensorFrequency")
        else:
            print("No settings available.")        
    except Exception as e:
        print(e)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("MQTT: Connected to MQTT Broker.")
        else:
            print("MQTT: Failed to connect, return code {0}".format(rc))
            return None

    # Set Connecting Client ID
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    print("MQTT: Connecting to server @ {0}:{1}".format(MQTT_SERVER, MQTT_PORT))
    client.connect(MQTT_SERVER, MQTT_PORT)
    return client


try:
    if DISPLAY_ATTACHED:
        with DISPLAY_LOCK:
            display = lcddriver.lcd()
            display.lcd_display_string("Initializing... ",1)
except Exception as e:
    print(e)
    print("Running headless: The display hardware does not appear attached")
    DISPLAY_ATTACHED = False

try:
    setupButton(BUTTON_PIN)
    temp_history = None
    humid_history = None

    last_temp = None
    last_humid = None
    allow_data_crushing = True
    rpi = RaspiCPU()
    ip_address = rpi.ip()

    if MQTT_ENABLED:
        mqtt_client = connect_mqtt()
        mqtt_client.loop_start()

    while True:
        start_time = time.time()
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        record_time = datetime.utcnow()

        if humidity is not None and temperature is not None:
            Fahrenheit = 9.0/5.0 * temperature + 32

            with DATA_LOCK:
                if temp_history is None:
                    temp_history = ValueHistory("temp","*F",DataPoint(Fahrenheit,record_time), HISTORY_LEN)
                temp_history.push(DataPoint(Fahrenheit,record_time))

                if humid_history is None:
                    humid_history = ValueHistory("hum","%",DataPoint(humidity,record_time), HISTORY_LEN)
                humid_history.push(DataPoint(humidity,record_time))

            UpdateDisplay()            

            hasChanged = True
            if allow_data_crushing and (not last_temp is None and last_temp == Fahrenheit) and (not last_humid is None and last_humid == humidity):
                hasChanged = False

            if hasChanged:
                cpu_temp = 9.0/5.0 * rpi.temp() + 32
            if MQTT_ENABLED:
                topic = MQTT_ROOT_TOPIC + "temperature"
                pubres = mqtt_client.publish(topic, Fahrenheit,0,True)
                pubres.wait_for_publish()
                print(pubres.rc)
                print("MQTT temp={0:.1f}F on topic={1}".format(Fahrenheit, topic))
                topic = MQTT_ROOT_TOPIC + "humidity"
                mqtt_client.publish(topic, humidity,0,True)
                print("MQTT hum={0:.1f}% on topic={1}".format(humidity, topic))

            last_temp = Fahrenheit
            last_humid = humidity

        else:
            if DISPLAY_ATTACHED:
                with DISPLAY_LOCK:
                    display.lcd_display_string(" Sensor Failed! ",1)
                    display.lcd_display_string("check connection",2)
            print("Failed to retrieve data from humidity sensor")

        elapsed_time = (time.time() - start_time) 
        if elapsed_time > UPDATE_INTERVAL:
            print("Update interval is too fast. Taking longer to read/render than the polling interval.")
        else:
            time.sleep(UPDATE_INTERVAL-elapsed_time)

except KeyboardInterrupt:
    if mqtt_client!= None:
        mqtt_client.loop_stop(True)

    if DISPLAY_ATTACHED:
        with DISPLAY_LOCK:
            display.lcd_clear()
    GPIO.cleanup()  
except Exception as e:
    if mqtt_client!= None:
        mqtt_client.loop_stop(True)

    GPIO.cleanup()  
    print(e)
    
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    
    if DISPLAY_ATTACHED:
        with DISPLAY_LOCK:
            display.lcd_clear()
            display.lcd_display_string("Error!          ",1)
            display.lcd_display_string(e,2)
    print("An error was encountered reading the sensor")
    
