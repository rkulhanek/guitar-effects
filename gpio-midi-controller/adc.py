#!/usr/bin/env python3

import time
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import matplotlib.pyplot as plt

def ohms(v: float) -> float:
	return (51000 * v) / (33.0 - 10.0 * v)

spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
cs = digitalio.DigitalInOut(board.D22)
mcp = MCP.MCP3008(spi, cs)
chan = AnalogIn(mcp, MCP.P0)

window = [ 0.05 ] * 60
window[1] = 22000
plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111)
line1, = ax.plot(window)

line1.set_ydata(window)
fig.canvas.draw()
fig.canvas.flush_events()
fig.canvas.mpl_connect('close_event', exit)

while True:
	window = [ ohms(chan.voltage) ] * 60
	line1.set_ydata(window)
	plt.title(f"{chan.value:5d} :: {chan.voltage:.2f}V :: {ohms(chan.voltage):5.0f}Ω")
	fig.canvas.draw()
	fig.canvas.flush_events()
	time.sleep(0.05)
