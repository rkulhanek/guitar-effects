#!/bin/env python3

# NOTE: Seems to work for the dirty bank but not clean?
# dirty *doesn't* have the checkmark in the midi setup dialog box
# Yep, that's what did it.

# NOTE: Don't use 0xFF for the "on" message value. Seems to be a magic number
# of some kind; jack's midi monitor program prints it differently.
# 64 works.

import rtmidi, time, sys, time, atexit, busio, board, digitalio, os, subprocess, sys
import RPi.GPIO as gpio
import adafruit_mcp3xxx.mcp3008 as MCP
from enum import IntEnum
from adafruit_mcp3xxx.analog_in import AnalogIn
from collections import namedtuple
from typing import List, Optional

atexit.register(gpio.cleanup)

MIDI_CHANNEL = 0
assert 0 <= MIDI_CHANNEL <= 0xF

PinInfo = namedtuple("PinInfo", "midi led")

Rheostat = namedtuple("Rheostat", "adc_chan midi_controller prev ")
class Rheostat:
	def __init__(self, adc_chan: AnalogIn, midi_controller: int):
		self.adc_chan = adc_chan
		self.midi_controller = midi_controller
		self.prev = -1
		

LED = IntEnum('LED', 
	{'BLUE0': 23, 'BLUE1': 18, 'BLUE2': 15, 'BLUE3': 14, 
	'RED': 17, 'YELLOW': 27, 'GREEN': 22, 'POWER': 26 })

TOGGLE_PEDAL = { # GPIO number -> MIDI controller number
	19: PinInfo(40, LED.BLUE0),
	13: PinInfo(41, LED.BLUE1),
	6: PinInfo(42, LED.BLUE2),
	5: PinInfo(43, LED.BLUE3),
}
rheostat_pedal: List[Rheostat] = []
switches = [ 25, 8, 7, 1 ]
POWER_BUTTON = 3

MAX_VALID_PRESET = 8

# TODO: have different default values for each pedal
# TODO: maybe have buttons that set all options at once, e.g. to toggle between dirty and clean
state = { k : True for k in TOGGLE_PEDAL.keys() }
skip_next = { k : False for k in TOGGLE_PEDAL.keys() }
midi_out = None

def shutdown() -> None:
	if midi_out:
		midi_out.delete()
	gpio.cleanup()
	
	# NOTE: not turning on yellow LED here because it turns off
	# *before* the shutdown sequence is complete
	os.system("shutdown -h now")

def status_led(color: str) -> None:
	# TODO: actually use this. Monitor the jackd logfile. Yellow if we've got recent xruns, red on error
	if 'red' == color:
		gpio.output(LED.RED, 1)
		gpio.output(LED.YELLOW, 0)
		gpio.output(LED.GREEN, 0)
	elif 'yellow' == color:
		gpio.output(LED.RED, 0)
		gpio.output(LED.YELLOW, 1)
		gpio.output(LED.GREEN, 0)
	elif 'green' == color:
		gpio.output(LED.RED, 0)
		gpio.output(LED.YELLOW, 0)
		gpio.output(LED.GREEN, 1)
	else:
		assert(0)

def set_status(severity: str, source: str, msg: Optional[str]) -> None:
	for a in [ 'Error', 'Warning' ]:
		if a not in set_status.__dict__:
			set_status.__dict__[a]: Dict[str,str] = {}

	info = set_status.__dict__[severity]
	if msg is None:
		if source in info:
			del info[source]
	else:
		info[source] = msg
		print(f"{severity}: {msg} ({source})")

	if len(set_status.Error):
		status_led('red')
	elif len(set_status.Warning):
		status_led('yellow')
	else:
		status_led('green')

def error(source: str, msg: Optional[str]) -> None:
	set_status('Error', source, msg)

def warning(source: str, msg: Optional[str]) -> None:
	set_status('Warning', source, msg)

def adc01(chan: AnalogIn) -> float:
	""" Returns value of MCP3008 channel `chan` normalized to [0,1] """
	MIN_VAL = 13300 # These were measured with a 5.1k resistor wired into the circuit.
	MAX_VAL = 63040 # They varied a bit between the two pedals, but not by enough to matter

	# TODO: maybe introduce a nonlinearity; it requires more force to move the first 50% than the second.
	# But see how it sounds before messing with it.
	v = float(chan.value) - MIN_VAL
	if v < 0.0:
		v = 0.0
	return v / (MAX_VAL - MIN_VAL)

def update_rheostats() -> None:
	""" Send midi signal if rheostat pedals have changed beyond a given threshold """
	threshold = 1
	for pedal in rheostat_pedal:
		val = int(0x7F * adc01(pedal.adc_chan))
		if abs(val - pedal.prev) > threshold:
			pedal.prev = val
			buf = [ 0xB0 | MIDI_CHANNEL, pedal.midi_controller, val ]
			midi_out.send_message(buf)

def toggle(pin: int) -> None:
	""" Send midi signal and set LED if pedal button pressed """

	# We see a rising edge when it's pressed *and* when it's released
	global state, skip_next
	if not skip_next[pin]:
		controller = TOGGLE_PEDAL[pin].midi

		assert midi_out is not None
		assert 0 <= controller <= 127
		buf = [ 0xB0 | MIDI_CHANNEL, controller, 0x7F if state[pin] else 0x00 ]
		gpio.output(TOGGLE_PEDAL[pin].led, int(state[pin]))
		#print(f"{buf}    led {TOGGLE_PEDAL[pin].led} = {int(state[pin])}")
		midi_out.send_message(buf)
		state[pin] = not state[pin]
	skip_next[pin] = not skip_next[pin]

def update_switches() -> None:
	""" Change presets if the switches have moved """
	preset = sum([ 2**idx * gpio.input(pin) for idx,pin in enumerate(switches) ])
	if preset != update_switches.__dict__.get('prev'):
		update_switches.prev = preset

		if preset <= MAX_VALID_PRESET:
			# send midi change program signal
			buf = [ 0xC0 | MIDI_CHANNEL, preset ]
			#print(f"Send {buf}")
			midi_out.send_message(buf)
			warning('update_switches', None)
		else:
			warning('update_switches', f'Invalid preset number: {preset}')
		


def setup_gpio() -> None:
	global state, rheostat_pedal
	gpio.setmode(gpio.BCM)
	#gpio.setup(16, gpio.OUT)

	# set up LED pins
	for pin in LED:
		gpio.setup(pin, gpio.OUT)
		gpio.output(pin, 0)
		
	for pin in switches:
		gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)

	# Toggle pedals
	for pin in TOGGLE_PEDAL.keys():
		gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)

		# TODO: This is picking up false positives. Set it up so it needs to receive a rising edge,
		# and then *stay* high for at least 50ms.
		# But first identify where the short circuit or loose wire is, because this signal gets sent when I bump the wires.
		# Okay, I was getting false positives when plugging a jumper into the Pi *when the other end of the jumper wasn't connected*. What the hell?
		#
		# And gpio.input() *always* reads 1. I'm wondering if the on-board pull up resistor is the issue. What if I wire it active high?
		# ...or what if I remove the resistor that's connecting Pi ground to breadboard ground?
		# ...that second one didn't help.
		#
		# Unrelated: for the final wiring, each LED needs its own resistor. They're too bright without one, and too dim
		# if they're all on the far end of the same one (They probably need fewer ohms each, as well).
		
		gpio.add_event_detect(pin, gpio.RISING, callback=toggle, bouncetime=20)

	#for k in TOGGLE_PEDAL.keys():
	#	state[k] = not state # Lets us initialize state with the desired values instead of inverse
	#	toggle(k)
	#	skip_next[k] = False
	
	# Power button
	gpio.output(LED.POWER, 1) # LED
	gpio.setup(3, gpio.IN) # Button

	# MCP3008 ADC
	spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
	cs = digitalio.DigitalInOut(board.D0)
	mcp = MCP.MCP3008(spi, cs)
	rheostat_pedal.append(Rheostat(AnalogIn(mcp, MCP.P6), 45))
	rheostat_pedal.append(Rheostat(AnalogIn(mcp, MCP.P7), 44))

def setup_midi() -> None:
	global midi_out
	midi_out = rtmidi.MidiOut()
	midi_out.open_virtual_port("gpio")

	dir = os.path.dirname(sys.argv[0])
	MAX_ATTEMPTS = 4
	for attempt in range(MAX_ATTEMPTS):
		if attempt > 0:
			sys.stderr.write(f"Attempt {attempt+1}...\n")
		r = subprocess.run(f"{dir}/connect_midi.sh")
		if 0 == r.returncode:
			return
		error('setup_midi', 'Failed to connect midi.\n')
	exit(1)

try:
	sys.stderr.write("setup_gpio\n")
	setup_gpio()
	sys.stderr.write("setup_midi\n")
	setup_midi()
	status_led('green')
	print("ready")
	while True:
		# TODO: see if preset toggle switches have changed
		# TODO: when toggle pedals pressed, send signal
		#print(f"{adc01(adc_chan6):.6f} --- {adc01(adc_chan7):.6f}")
		update_rheostats()
		update_switches()
		if gpio.input(POWER_BUTTON):
			shutdown()
		time.sleep(0.05)
except KeyboardInterrupt:
	# TODO: make this happen on shutdown, too. Trivial once
	# all the code is in the one script.
	if midi_out:
		midi_out.delete()

