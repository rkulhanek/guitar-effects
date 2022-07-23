#!/usr/bin/env python3

import time, atexit
import busio
import digitalio
import board
import RPi.GPIO as gpio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import matplotlib.pyplot as plt

def ohms(v: float) -> float:
	return (51000 * v) / (33.0 - 10.0 * v)

minval = 13300
maxval = 63040
def val01(v: int) -> float:
	v = float(v) - minval
	if v < 0.0:
		v = 0.0
	return v / (maxval - minval)

atexit.register(gpio.cleanup)


try:
	print('Try')
	spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
	cs = digitalio.DigitalInOut(board.D0)
	mcp = MCP.MCP3008(spi, cs)
	chan6 = AnalogIn(mcp, MCP.P6)
	chan7 = AnalogIn(mcp, MCP.P7)

	N = 30
	window = [ 0.01 ] * (N*2)
	window[1] = 1.0
	plt.ion()
	fig = plt.figure()
	ax = fig.add_subplot(111)
	line1, = ax.plot(window)

	line1.set_ydata(window)
	fig.canvas.draw()
	fig.canvas.flush_events()
	fig.canvas.mpl_connect('close_event', exit)

	while True:
		window = [ val01(chan6.value) ] * N + [ val01(chan7.value) ] * N
		line1.set_ydata(window)
		plt.title(
			f"{chan6.value:5d} :: {chan6.voltage:.2f}V :: {ohms(chan6.voltage):5.0f}Ω :: {val01(chan6.value):.6f}\n"
			+ f"{chan7.value:5d} :: {chan7.voltage:.2f}V :: {ohms(chan7.voltage):5.0f}Ω :: {val01(chan7.value):.6f}")
		fig.canvas.draw()
		fig.canvas.flush_events()
		time.sleep(0.05)
except KeyboardInterrupt:
	pass


