#!/bin/env python3

# TODO: Avoid having any auto-started code that will shutdown the system immediately if the gpio
# doesn't have the right connections. Maybe put a delay on the shutdown if it's triggered before
# the system has been online for 2 minutes
# (Worst case, I can always pop the SD card out and modify things from there, but better to avoid the need)

import time, os
import RPi.GPIO as gpio

def shutdown(pin: int) -> None:
	os.system("shutdown -h now")

def setup_gpio() -> None:
	global state
	gpio.setmode(gpio.BCM)
	pin = 3
	gpio.setup(pin, gpio.IN)
	gpio.add_event_detect(pin, gpio.RISING, callback=shutdown, bouncetime=500)

try:
	setup_gpio()
	while True:
		time.sleep(0.01)
except KeyboardInterrupt:
	gpio.cleanup()
