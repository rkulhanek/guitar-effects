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
chan6 = AnalogIn(mcp, MCP.P6)
chan7 = AnalogIn(mcp, MCP.P7)

N = 30
window = [ 0.05 ] * (N*2)
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
	window = [ ohms(chan6.voltage) ] * N + [ ohms(chan7.voltage) ] * N
	line1.set_ydata(window)
	plt.title(
		f"{chan6.value:5d} :: {chan6.voltage:.2f}V :: {ohms(chan6.voltage):5.0f}Ω\n"
		+ f"{chan7.value:5d} :: {chan7.voltage:.2f}V :: {ohms(chan7.voltage):5.0f}Ω")
	fig.canvas.draw()
	fig.canvas.flush_events()
	time.sleep(0.05)
