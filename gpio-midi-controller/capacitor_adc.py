#!/usr/bin/env python3

#         1K ohm
# 3.3V -/\/\/\/---/\/\/\/
#                    ^
#        PIN --------|
#                    |
#                    = 10 uF
#                    |
#        GND---------|

# TODO: play around with resistor value. More ohms means lower frequency
# but probably also more consistency
# Might also use the average of the last k readings to average out the noise

import time, os, RPi.GPIO as gpio
PIN = 16
WINDOW_SIZE = 10
gpio.setmode(gpio.BCM)

def listen_mode():
	def RCtime():
		gpio.setup(PIN, gpio.OUT)
		gpio.output(PIN, gpio.LOW)
		time.sleep(0.1)
		
		# TODO: I don't want this sitting in a hot idle loop. Can I use an interrupt?
		gpio.setup(PIN, gpio.IN)
		t = time.clock_gettime_ns(time.CLOCK_PROCESS_CPUTIME_ID)
		while (gpio.input(PIN) == gpio.LOW):
			pass
		return time.clock_gettime_ns(time.CLOCK_PROCESS_CPUTIME_ID) - t

	window = [RCtime()] * WINDOW_SIZE
	t_sum = sum(window)

	idx = 0
	while True:
		# smooth out signal
		idx = (idx + 1) % WINDOW_SIZE
		t_sum -= window[idx]
		window[idx] = RCtime()
		t_sum += window[idx]

		print(t_sum)

		time.sleep(0.1)

def interrupt_mode():
	# TODO: I don't want this sitting in a hot idle loop. Can I use an interrupt?
	t = time.clock_gettime_ns(time.CLOCK_PROCESS_CPUTIME_ID)
	def ping():
		nonlocal t
		gpio.remove_event_detect(PIN)
		gpio.setup(PIN, gpio.OUT)
		gpio.output(PIN, gpio.LOW)
		time.sleep(0.1)
	
		gpio.setup(PIN, gpio.IN)
		gpio.add_event_detect(PIN, gpio.RISING, callback=ping, bouncetime=10)
		t2 = time.clock_gettime_ns(time.CLOCK_PROCESS_CPUTIME_ID)
		print(t2 - t1) # real version, this'll send a midi message iff it differs by more than noise
		t = t2
	
	# TODO: I don't want this sitting in a hot idle loop. Can I use an interrupt?
	ping()
interrupt_mode()
