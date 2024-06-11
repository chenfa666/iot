import os
import time
import schedule
from Adafruit_IO import Client, RequestError
import rs485

AIO_FEED_ID = ["humid", "light"]
AIO_USERNAME = os.getenv('AIO_USERNAME')
AIO_KEY = os.getenv('AIO_KEY')

if not AIO_USERNAME or not AIO_KEY:
    print("Missing Adafruit IO credentials")
    exit()

aio = Client(AIO_USERNAME, AIO_KEY)

def test_sensors():
    while True:
        print("Testing sensors")
        moisture = rs485.read_moisture()
        temperature = rs485.read_temperature()
        
        print(f"Moisture: {moisture}")
        print(f"Temperature: {temperature}")
        
        try:
            aio.send(AIO_FEED_ID[0], moisture)
            aio.send(AIO_FEED_ID[1], temperature)
        except RequestError as e:
            print(f"Error sending data to Adafruit IO: {e}")

        time.sleep(2)

def activate_relay_with_timeout(relay_id, timeout):
    rs485.set_device_state(relay_id, True)
    time.sleep(timeout)
    rs485.set_device_state(relay_id, False)

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

def scheduled_irrigation_workflow():
    print("Scheduled irrigation workflow started")
    irrigation_workflow()

def schedule_tasks():
    # Schedule the irrigation workflow at specific times
    schedule.every().day.at("06:00").do(scheduled_irrigation_workflow)
    schedule.every().day.at("18:00").do(scheduled_irrigation_workflow)

    # Run the scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Run the sensor testing in a separate thread
    import threading
    sensor_thread = threading.Thread(target=test_sensors)
    sensor_thread.start()

    # Start the scheduler
    schedule_tasks()