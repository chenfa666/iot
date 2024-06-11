import os
import time
import serial
import serial.tools.list_ports
from Adafruit_IO import Client, RequestError

def add_modbus_crc(msg):
    crc = 0xFFFF
    for n in range(len(msg)):
        crc ^= msg[n]
        for i in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    ba = crc.to_bytes(2, byteorder='little')
    msg.append(ba[0])
    msg.append(ba[1])
    return msg

def get_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "USB" in str(port):
            return port.device
    return "/dev/ttyUSB1"  # Default port

port_name = get_port()
print(f"Using port: {port_name}")

try:
    ser = serial.Serial(port=port_name, baudrate=9600)
    print("Serial port opened successfully")
except serial.SerialException as e:
    print(f"Failed to open serial port: {e}")
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
    2: {'on': [2, 6, 0, 0, 0, 255], 'off': [2, 6, 0, 0, 0, 0]},
    3: {'on': [3, 6, 0, 0, 0, 255], 'off': [3, 6, 0, 0, 0, 0]},
    4: {'on': [4, 6, 0, 0, 0, 255], 'off': [4, 6, 0, 0, 0, 0]},
    5: {'on': [5, 6, 0, 0, 0, 255], 'off': [5, 6, 0, 0, 0, 0]},
    6: {'on': [6, 6, 0, 0, 0, 255], 'off': [6, 6, 0, 0, 0, 0]},
    7: {'on': [7, 6, 0, 0, 0, 255], 'off': [7, 6, 0, 0, 0, 0]},
    8: {'on': [8, 6, 0, 0, 0, 255], 'off': [8, 6, 0, 0, 0, 0]},
}

def set_device_state(id, state):
    if id in relay_commands:
        command = relay_commands[id]['on'] if state else relay_commands[id]['off']
        try:
            ser.write(add_modbus_crc(command))
        except serial.SerialException as e:
            print(f"Failed to write to serial port: {e}")
    else:
        print(f"Invalid relay ID: {id}")

def serial_read_data():
    try:
        bytes_to_read = ser.inWaiting()
        if bytes_to_read > 0:
            out = ser.read(bytes_to_read)
            data_array = [b for b in out]
            if len(data_array) >= 7:
                value = data_array[-4] * 256 + data_array[-3]
                return value
            else:
                return -1
        return 0
    except serial.SerialException as e:
        print(f"Failed to read from serial port: {e}")
        return None

# Sensor commands
soil_temperature_command = [1, 3, 0, 6, 0, 1]
soil_moisture_command = [1, 3, 0, 7, 0, 1]

def read_temperature():
    serial_read_data()
    ser.write(add_modbus_crc(soil_temperature_command))
    time.sleep(1)
    return serial_read_data()

def read_moisture():
    serial_read_data()
    ser.write(add_modbus_crc(soil_moisture_command))
    time.sleep(1)
    return serial_read_data()

def test_sensors():
    while True:
        print("Testing sensors")
        moisture = read_moisture()
        temperature = read_temperature()
        
        print(f"Moisture: {moisture}")
        print(f"Temperature: {temperature}")
        
        try:
            aio.send(AIO_FEED_ID[0], moisture)
            aio.send(AIO_FEED_ID[1], temperature)
        except RequestError as e:
            print(f"Error sending data to Adafruit IO: {e}")

        time.sleep(2)

# Workflow and relay activation
def activate_relay_with_timeout(relay_id, timeout):
    set_device_state(relay_id, True)
    time.sleep(timeout)
    set_device_state(relay_id, False)

def irrigation_workflow():
    # Fertilizer mixers (IDs 1, 2, 3)
    for mixer_id in range(1, 4):
        print(f"Activating fertilizer mixer {mixer_id}")
        activate_relay_with_timeout(mixer_id, 10)  # 10 seconds for demo
    
    # Area selectors (IDs 4, 5, 6)
    for area_id in range(4, 7):
        print(f"Activating area selector {area_id}")
        activate_relay_with_timeout(area_id, 5)  # 5 seconds for demo

    # Pump in (ID 7)
    print("Activating pump in")
    activate_relay_with_timeout(7, 20)  # 20 seconds for demo

    # Pump out (ID 8)
    print("Activating pump out")
    activate_relay_with_timeout(8, 10)  # 10 seconds for demo

# Run the workflow
irrigation_workflow()

# Test sensors continuously
test_sensors()

# Close serial connection (not reachable due to the infinite loop in test_sensors)
ser.close()
