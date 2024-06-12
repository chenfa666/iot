import os
import time
import schedule
import threading
import paho.mqtt.client as mqtt
from Adafruit_IO import Client, RequestError
import rs485

# Adafruit IO credentials
AIO_USERNAME = ""
AIO_KEY = ""

if not AIO_USERNAME or not AIO_KEY:
    print("Missing Adafruit IO credentials")
    exit()

# Initialize Adafruit IO client
aio = Client(AIO_USERNAME, AIO_KEY)

# Adafruit IO feed IDs
AIO_FEED_ID = ["humid", "temp", "state", "schedule"]

# List to store schedule jobs
schedule_times = ["06:00", "18:00"]

def send_state_to_aio(state):
    try:
        aio.send(AIO_FEED_ID[2], state)
    except RequestError as e:
        print(f"Error sending state to Adafruit IO: {e}")

def send_schedule_to_aio():
    try:
        schedule_str = ",".join(schedule_times)
        aio.send(AIO_FEED_ID[3], schedule_str)
    except RequestError as e:
        print(f"Error sending schedule to Adafruit IO: {e}")

def test_sensors():
    while True:
        try:
            print("Testing sensors")
            moisture = rs485.read_moisture()/100
            temperature = rs485.read_temperature()/100
        
            print(f"Moisture: {moisture}")
            print(f"Temperature: {temperature}")
        
            aio.send(AIO_FEED_ID[0], moisture)
            aio.send(AIO_FEED_ID[1], temperature)
        except Exception as e:
            print(f"Error in test_sensors: {e}")

        time.sleep(2)

def activate_relay_with_timeout(relay_id, timeout):
    try:
        rs485.set_device_state(relay_id, True)
        time.sleep(timeout)
        rs485.set_device_state(relay_id, False)
    except Exception as e:
        print(f"Error in activate_relay_with_timeout: {e}")

def irrigation_workflow():
     # State: MIXER 1
    current_state = "MIXER 1"
    print(f"Activating {current_state}")
    send_state_to_aio(AIO_FEED_ID[2], current_state)
    activate_relay_with_timeout(1, 10)  # 10 seconds for demo

    # State: MIXER 2
    current_state = "MIXER 2"
    print(f"Activating {current_state}")
    send_state_to_aio(AIO_FEED_ID[2], current_state)
    activate_relay_with_timeout(2, 10)  # 10 seconds for demo

    # State: MIXER 3
    current_state = "MIXER 3"
    print(f"Activating {current_state}")
    send_state_to_aio(AIO_FEED_ID[2], current_state)
    activate_relay_with_timeout(3, 10)  # 10 seconds for demo

    # State: PUMP IN
    current_state = "PUMP IN"
    print(f"Activating {current_state}")
    send_state_to_aio(AIO_FEED_ID[2], current_state)
    activate_relay_with_timeout(7, 20)  # 20 seconds for demo

    # State: SELECTOR
    for area_id in range(4, 7):
        current_state = f"SELECTOR {area_id}"
        print(f"Activating {current_state}")
        send_state_to_aio(AIO_FEED_ID[2], current_state)
        activate_relay_with_timeout(area_id, 5)  # 5 seconds for demo

        # State: PUMP OUT at each area
        current_state = f"PUMP OUT at area {area_id}"
        print(f"Activating {current_state}")
        send_state_to_aio(AIO_FEED_ID[2], current_state)
        activate_relay_with_timeout(8, 10)  # 10 seconds for demo

    # State: NEXT CYCLE (loop back to IDLE)
    current_state = "NEXT CYCLE"
    print(f"Cycle complete, returning to {current_state}")
    send_state_to_aio(AIO_FEED_ID[2], current_state)

def scheduled_irrigation_workflow():
    print("Scheduled irrigation workflow started")
    irrigation_workflow()

def add_schedule(schedule_time):
    if schedule_time not in schedule_times:
        schedule_times.append(schedule_time)
        send_schedule_to_aio()
        print(f"Added schedule for {schedule_time}")
    else:
        print(f"Schedule for {schedule_time} already exists")

def remove_schedule(schedule_time):
    if schedule_time in schedule_times:
        schedule_times.remove(schedule_time)
        send_schedule_to_aio()
        print(f"Removed schedule for {schedule_time}")
    else:
        print(f"No schedule found for {schedule_time}")

def schedule_tasks():
    # Schedule the irrigation workflow at specific times
    while True:
        for schedule_time in schedule_times:
            schedule.every().day.at(schedule_time).do(scheduled_irrigation_workflow)
        
        # Run the scheduled tasks
        schedule.run_pending()
        time.sleep(1)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to command feed for scheduling
    client.subscribe(f"{AIO_USERNAME}/feeds/command")

def on_message(client, userdata, msg):
    print(f"Received value: {msg.payload.decode()} from topic: {msg.topic}")
    payload = msg.payload.decode().strip().lower()
    
    if payload.startswith("add"):
        schedule_time = payload.split(" ")[1]
        add_schedule(schedule_time)
    
    elif payload.startswith("remove"):
        schedule_time = payload.split(" ")[1]
        remove_schedule(schedule_time)

if __name__ == "__main__":
    # Start MQTT client
    client = mqtt.Client()
    client.username_pw_set(AIO_USERNAME, AIO_KEY)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("io.adafruit.com", 1883, 60)
    client.loop_start()  # Start the MQTT client in a background thread

    # Run the sensor testing in a separate thread
    sensor_thread = threading.Thread(target=test_sensors)
    sensor_thread.start()

    # Send initial schedule to Adafruit IO
    send_schedule_to_aio()

    # Start the scheduler
    schedule_thread = threading.Thread(target=schedule_tasks)
    schedule_thread.start()
