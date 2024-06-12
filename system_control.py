import os
import time
import schedule
from Adafruit_IO import Client, RequestError
import rs485
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv() 

AIO_FEED_ID = ["humid", "temp", "state", "schedule"]
AIO_USERNAME = os.getenv('AIO_USERNAME')
AIO_KEY = os.getenv('AIO_KEY')

if not AIO_USERNAME or not AIO_KEY:
    print("Missing Adafruit IO credentials")
    exit()

aio = Client(AIO_USERNAME, AIO_KEY)
scheduled_jobs = {}

def send_state_to_aio(feed_id, state):
    try:
        aio.send(feed_id, state)
    except RequestError as e:
        print(f"Error sending {feed_id} state to Adafruit IO: {e}")

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

def schedule_tasks():
    # Schedule the irrigation workflow at specific times
    add_schedule("06:00")
    add_schedule("18:00")
    send_state_to_aio(AIO_FEED_ID[3], "Scheduled tasks initialized")

    # Run the scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)

def add_schedule(time_str):
    job = schedule.every().day.at(time_str).do(scheduled_irrigation_workflow)
    scheduled_jobs[time_str] = job
    send_state_to_aio(AIO_FEED_ID[3], f"Added schedule at {time_str}")
    list_schedules()  # Update the schedule feed on Adafruit IO

def remove_schedule(time_str):
    job = scheduled_jobs.pop(time_str, None)
    if job:
        schedule.cancel_job(job)
        send_state_to_aio(AIO_FEED_ID[3], f"Removed schedule at {time_str}")
    else:
        send_state_to_aio(AIO_FEED_ID[3], f"No schedule found at {time_str}")
    list_schedules()  # Update the schedule feed on Adafruit IO

def remove_all_schedules():
    schedule.clear()
    scheduled_jobs.clear()
    send_state_to_aio(AIO_FEED_ID[3], "All schedules cleared")
    list_schedules()  # Update the schedule feed on Adafruit IO

def list_schedules():
    jobs = schedule.get_jobs()
    job_list = [str(job) for job in jobs]
    if job_list:
        schedule_str = "\n".join(job_list)
    else:
        schedule_str = "No schedules found."
    send_state_to_aio(AIO_FEED_ID[3], schedule_str)
    print(f"Current schedules: {schedule_str}")

if __name__ == "__main__":
    # Run the sensor testing in a separate thread
    sensor_thread = threading.Thread(target=test_sensors)
    sensor_thread.start()

    # Start the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=schedule_tasks)
    scheduler_thread.start()
