import os
import time
import serial.tools.list_ports
from Adafruit_IO import Client, Feed, RequestError

def getPort():
    ports = serial.tools.list_ports.comports()
    N = len(ports)
    commPort = "None"
    for i in range(0, N):
        port = ports[i]
        strPort = str(port)
        if "USB" in strPort:
            splitPort = strPort.split(" ")
            commPort = (splitPort[0])
    return commPort

portName = getPort()
if portName == "None":
    portName = "/dev/ttyUSB1"

print(portName)

try:
    ser = serial.Serial(port=portName, baudrate=115200)
    print("Opened successfully")
except:
    print("Cannot open the port")
    exit()

# Adafruit IO setup
AIO_FEED_ID = ["humid", "light"]
AIO_USERNAME = os.getenv('AIO_USERNAME')
AIO_KEY = os.getenv('AIO_KEY')

if not AIO_USERNAME or not AIO_KEY:
    print("Missing Adafruit IO credentials")
    exit()

aio = Client(AIO_USERNAME, AIO_KEY)

# Relay commands
relay_commands = {
    1: {'on': [1, 6, 0, 0, 0, 255], 'off': [1, 6, 0, 0, 0, 0]},
    2: {'on': [2, 6, 0, 1, 0, 255], 'off': [2, 6, 0, 1, 0, 0]},
    3: {'on': [3, 6, 0, 2, 0, 255], 'off': [3, 6, 0, 2, 0, 0]},
    4: {'on': [4, 6, 0, 3, 0, 255], 'off': [4, 6, 0, 3, 0, 0]},
    5: {'on': [5, 6, 0, 4, 0, 255], 'off': [5, 6, 0, 4, 0, 0]},
    6: {'on': [6, 6, 0, 5, 0, 255], 'off': [6, 6, 0, 5, 0, 0]},
    7: {'on': [7, 6, 0, 6, 0, 255], 'off': [7, 6, 0, 6, 0, 0]},
    8: {'on': [8, 6, 0, 7, 0, 255], 'off': [8, 6, 0, 7, 0, 0]},
}

def setRelay(relay_id, state):
    if relay_id in relay_commands:
        command = relay_commands[relay_id]['on'] if state else relay_commands[relay_id]['off']
        ser.write(command)
        time.sleep(1)
        print(serial_read_data(ser))
    else:
        print(f"Invalid relay ID: {relay_id}")

def serial_read_data(ser):
    bytesToRead = ser.inWaiting()
    if bytesToRead > 0:
        out = ser.read(bytesToRead)
        data_array = [b for b in out]
        print(data_array)
        if len(data_array) >= 7:
            array_size = len(data_array)
            value = data_array[array_size - 4] * 256 + data_array[array_size - 3]
            return value
        else:
            return -1
    return 0

# Timer-based relay activation
def activateRelayWithTimeout(relay_id, timeout):
    setRelay(relay_id, True)
    time.sleep(timeout)
    setRelay(relay_id, False)

# Example workflow
def irrigationWorkflow():
    # Fertilizer mixers (IDs 1, 2, 3)
    for mixer_id in range(1, 4):
        print(f"Activating fertilizer mixer {mixer_id}")
        activateRelayWithTimeout(mixer_id, 10)  # 10 seconds for demo
    
    # Area selectors (IDs 4, 5, 6)
    for area_id in range(4, 7):
        print(f"Activating area selector {area_id}")
        activateRelayWithTimeout(area_id, 5)  # 5 seconds for demo

    # Pump in (ID 7)
    print("Activating pump in")
    activateRelayWithTimeout(7, 20)  # 20 seconds for demo

    # Pump out (ID 8)
    print("Activating pump out")
    activateRelayWithTimeout(8, 10)  # 10 seconds for demo

# Sensor commands
soil_temperature = [1, 3, 0, 6, 0, 1, 100, 11]
def readTemperature():
    serial_read_data(ser)
    ser.write(soil_temperature)
    time.sleep(1)
    return serial_read_data(ser)

soil_moisture = [1, 3, 0, 7, 0, 1, 53, 203]
def readMoisture():
    serial_read_data(ser)
    ser.write(soil_moisture)
    time.sleep(1)
    return serial_read_data(ser)

def testSensors():
    while True:
        print("TEST SENSOR")
        moisture = readMoisture()
        temperature = readTemperature()
        
        print(f"Moisture: {moisture}")
        print(f"Temperature: {temperature}")
        
        try:
            aio.send(AIO_FEED_ID[0], moisture)
            aio.send(AIO_FEED_ID[1], temperature)
        except RequestError as e:
            print(f"Error sending data to Adafruit IO: {e}")

        time.sleep(2)

# Run the workflow
irrigationWorkflow()

# Test sensors continuously
testSensors()

# Close serial connection (not reachable due to the infinite loop in testSensors)
ser.close()
