import os
import time
import schedule
from Adafruit_IO import Client, RequestError
import rs485

AIO_FEED_ID = ["humid", "light", "state", "schedule"]
AIO_USERNAME = os.getenv('AIO_USERNAME')
AIO_KEY = os.getenv('AIO_KEY')

if not AIO_USERNAME or not AIO_KEY:
    print("Missing Adafruit IO credentials")
    exit()

aio = Client(AIO_USERNAME, AIO_KEY)

def send_state_to_aio(state):
    try:
        aio.send(AIO_FEED_ID[2], state)
    except RequestError as e:
        print(f"Error sending state to Adafruit IO: {e}")

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
    current_state = "MIXER 1"
    print(f"Activating {current_state}")
    send_state_to_aio(current_state)
    activate_relay_with_timeout(1, 10)

    current_state = "MIXER 2"
    print(f"Activating {current_state}")
    send_state_to_aio(current_state)
    activate_relay_with_timeout(2, 10)

    current_state = "MIXER 3"
    print(f"Activating {current_state}")
    send_state_to_aio(current_state)
    activate_relay_with_timeout(3, 10)

    current_state = "PUMP IN"
    print(f"Activating {current_state}")
    send_state_to_aio(current_state)
    activate_relay_with_timeout(7, 20)

    for area_id in range(4, 7):
        current_state = f"SELECTOR {area_id}"
        print(f"Activating {current_state}")
        send_state_to_aio(current_state)
        activate_relay_with_timeout(area_id, 5)

        current_state = f"PUMP OUT at area {area_id}"
        print(f"Activating {current_state}")
        send_state_to_aio(current_state)
        activate_relay_with_timeout(8, 10)

    current_state = "NEXT CYCLE"
    print(f"Cycle complete, returning to {current_state}")
    send_state_to_aio(current_state)

def scheduled_irrigation_workflow():
    print("Scheduled irrigation workflow started")
    irrigation_workflow()

def schedule_tasks():
    schedule.every().day.at("06:00").do(scheduled_irrigation_workflow)
    schedule.every().day.at("18:00").do(scheduled_irrigation_workflow)

    while True:
        schedule.run_pending()
        time.sleep(1)

def add_schedule(time_str):
    with schedule_lock:
        schedule.every().day.at(time_str).do(scheduled_irrigation_workflow)
    print(f"Added schedule: {time_str}")

def remove_schedule(time_str):
    with schedule_lock:
        job_found = False
        for job in schedule.jobs:
            if job.at_time == time_str:
                schedule.cancel_job(job)
                job_found = True
                break
    if job_found:
        print(f"Removed schedule: {time_str}")
    else:
        print(f"No schedule found at: {time_str}")

def handle_schedule_commands():
    while True:
        try:
            command = aio.receive(AIO_FEED_ID[3]).value

            if command:
                action, time_str = command.split(',')
                if action == 'add':
                    add_schedule(time_str)
                elif action == 'remove':
                    remove_schedule(time_str)
                aio.send(AIO_FEED_ID[3], "")  # Clear the command after processing

        except RequestError as e:
            print(f"Error handling schedule commands: {e}")
        except ValueError as ve:
            print(f"Invalid command format: {ve}")

        time.sleep(5)  # Check for new commands every 5 seconds

if __name__ == "__main__":
    import threading
    schedule_lock = threading.Lock()

    sensor_thread = threading.Thread(target=test_sensors)
    sensor_thread.start()

    command_thread = threading.Thread(target=handle_schedule_commands)
    command_thread.start()

    schedule_tasks()
