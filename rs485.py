import time
import serial
import serial.tools.list_ports

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
            print(f"Raw data received: {out}")  # Debugging line
            data_array = [b for b in out]
            print(f"Data array: {data_array}")  # Debugging line
            if len(data_array) >= 7:
                value = data_array[-4] * 256 + data_array[-3]
                return value
            else:
                print("Data array length is less than expected")  # Debugging line
                return -1
        return 0
    except serial.SerialException as e:
        print(f"Failed to read from serial port: {e}")
        return None

# Sensor commands
soil_temperature_command = [1, 3, 0, 6, 0, 1]
soil_moisture_command = [1, 3, 0, 7, 0, 1]

def read_temperature():
    serial_read_data()  # Clear buffer before sending command
    ser.write(add_modbus_crc(soil_temperature_command))
    time.sleep(1)
    return serial_read_data()

def read_moisture():
    serial_read_data()  # Clear buffer before sending command
    ser.write(add_modbus_crc(soil_moisture_command))
    time.sleep(1)
    return serial_read_data()
