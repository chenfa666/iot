import time
import serial.tools.list_ports

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

# Relay commands
relay_commands = {
    1: {'on': [0, 6, 0, 0, 0, 255, 200, 91], 'off': [0, 6, 0, 0, 0, 0, 136, 27]},
    2: {'on': [0, 6, 0, 1, 0, 255, 201, 220], 'off': [0, 6, 0, 1, 0, 0, 137, 156]},
    3: {'on': [0, 6, 0, 2, 0, 255, 203, 85], 'off': [0, 6, 0, 2, 0, 0, 139, 21]},
    4: {'on': [0, 6, 0, 3, 0, 255, 204, 180], 'off': [0, 6, 0, 3, 0, 0, 140, 116]},
    5: {'on': [0, 6, 0, 4, 0, 255, 206, 45], 'off': [0, 6, 0, 4, 0, 0, 142, 237]},
    6: {'on': [0, 6, 0, 5, 0, 255, 207, 140], 'off': [0, 6, 0, 5, 0, 0, 143, 76]},
    7: {'on': [0, 6, 0, 6, 0, 255, 209, 5], 'off': [0, 6, 0, 6, 0, 0, 145, 141]},
    8: {'on': [0, 6, 0, 7, 0, 255, 210, 100], 'off': [0, 6, 0, 7, 0, 0, 146, 236]},
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
soil_temperature =[1, 3, 0, 6, 0, 1, 100, 11]
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
        print(readMoisture())
        time.sleep(1)
        print(readTemperature())
        time.sleep(1)

# Run the workflow
irrigationWorkflow()

# Test sensors continuously
testSensors()

# Close serial connection (not reachable due to the infinite loop in testSensors)
ser.close()
