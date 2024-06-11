# system_control.py

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

def scheduled_irrigation_workflow():
    print("Scheduled irrigation workflow started")
    rs485.irrigation_workflow()

def schedule_tasks():
    # Schedule the irrigation workflow at specific times
    schedule.every().day.at("06:00").do(scheduled_irrigation_workflow)
    schedule.every().day.at("18:00").do(scheduled_irrigation_workflow)

    # Run the scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # Run the sensor testing in a separate thread or process if needed
    # For now, we'll run it sequentially in this example
    import threading
    sensor_thread = threading.Thread(target=test_sensors)
    sensor_thread.start()

    # Start the scheduler
    schedule_tasks()
