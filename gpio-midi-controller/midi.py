#!/bin/env python3

# NOTE: Seems to work for the dirty bank but not clean?
# dirty *doesn't* have the checkmark in the midi setup dialog box
# Yep, that's what did it.

# NOTE: Don't use 0xFF for the "on" message value. Seems to be a magic number
# of some kind; jack's midi monitor program prints it differently.
# 64 works.

import rtmidi, time, sys, time, atexit, busio, board, digitalio
import RPi.GPIO as gpio
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
from collections import namedtuple

atexit.register(gpio.cleanup)

MIDI_CHANNEL = 0
assert 0 <= MIDI_CHANNEL <= 0xF

PinInfo = namedtuple("PinInfo", "midi led")

TOGGLE_PEDAL = { # GPIO number -> MIDI controller number
	5: PinInfo(40, 14),
	6: PinInfo(41, 15),
	13: PinInfo(42, 18),
	19: PinInfo(43, 23),
}
POWER_LIGHT = 26

# TODO: have different default values for each pedal
# TODO: maybe have buttons that set all options at once, e.g. to toggle between dirty and clean
state = { k : True for k in TOGGLE_PEDAL.keys() }
skip_next = { k : False for k in TOGGLE_PEDAL.keys() }
midi_out = None

def status(color: str) -> None:
	# TODO: actually use this. Monitor the jackd logfile. Yellow if we've got recent xruns, red on error
	if 'red' == color:
		gpio.output(27, 0)
		gpio.output(22, 0)
		gpio.output(17, 1)
	if 'yellow' == color:
		gpio.output(17, 0)
		gpio.output(22, 0)
		gpio.output(27, 1)
	elif 'green' == color:
		gpio.output(17, 0)
		gpio.output(27, 0)
		gpio.output(22, 1)
	else:
		assert(0)

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

def toggle(pin: int) -> None:
	# We see a rising edge when it's pressed *and* when it's released
	global state, skip_next
	if not skip_next[pin]:
		controller = TOGGLE_PEDAL[pin].midi

		assert midi_out is not None
		assert 0 <= controller <= 127
		buf = [ 0xB0 | MIDI_CHANNEL, controller, 64 if state[pin] else 0x00 ]
		gpio.output(TOGGLE_PEDAL[pin].led, int(state[pin]))
		print(f"{buf}    led {TOGGLE_PEDAL[pin].led} = {int(state[pin])}")
		midi_out.send_message(buf)
		state[pin] = not state[pin]
	skip_next[pin] = not skip_next[pin]

def change_preset(preset: int) -> None:
	buf = [ 0xC0 | MIDI_CHANNEL, preset ]
	print(f"Send {buf}")
	midi_out.send_message(buf)

def setup_gpio() -> None:
	global state, adc_chan6, adc_chan7
	gpio.setmode(gpio.BCM)
	#gpio.setup(16, gpio.OUT)

	# RYG pins
	gpio.setup(17, gpio.OUT)
	gpio.setup(22, gpio.OUT)
	gpio.setup(27, gpio.OUT)

	# Toggle pedals
	for pin in TOGGLE_PEDAL.keys():
		gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
		gpio.setup(TOGGLE_PEDAL[pin].led, gpio.OUT)
		gpio.output(TOGGLE_PEDAL[pin].led, 0)

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

	for k in TOGGLE_PEDAL.keys():
		state[k] = not state # Lets us initialize state with the desired values instead of inverse
		toggle(k)
		skip_next[k] = False
	
	# Power button
	gpio.setup(POWER_LIGHT, gpio.OUT)
	gpio.output(POWER_LIGHT, 1) # LED
	gpio.setup(3, gpio.IN) # Button

	# MCP3008 ADC
	spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
	cs = digitalio.DigitalInOut(board.D0)
	mcp = MCP.MCP3008(spi, cs)
	adc_chan6 = AnalogIn(mcp, MCP.P6)
	adc_chan7 = AnalogIn(mcp, MCP.P7)

def setup_midi() -> None:
	global midi_out
	midi_out = rtmidi.MidiOut()
	midi_out.open_virtual_port("gpio")

try:
	sys.stderr.write("setup_midi\n")
	sys.stderr.flush();
	setup_midi()
	sys.stderr.write("setup_gpio\n")
	sys.stderr.flush();
	setup_gpio()
	status('green')
	print("ready")
	#change_preset(1)
	while True:
		# TODO: see if preset toggle switches have changed
		# TODO: shutdown if power button off (be sure to call gpio.cleanup()
		# TODO: if adc difference exceeds (small) threshold, send midi signal
		# TODO: when toggle pedals pressed, send signal
		#print(f"{adc01(adc_chan6):.6f} --- {adc01(adc_chan7):.6f}")
		time.sleep(0.1)
except KeyboardInterrupt:
	# TODO: make this happen on shutdown, too. Trivial once
	# all the code is in the one script.
	if midi_out:
		midi_out.delete()
		del midi_out

