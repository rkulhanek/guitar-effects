#!/bin/env python3

# NOTE: Seems to work for the dirty bank but not clean?
# dirty *doesn't* have the checkmark in the midi setup dialog box
# Yep, that's what did it.

# NOTE: Don't use 0xFF for the "on" message value. Seems to be a magic number
# of some kind; jack's midi monitor program prints it differently.
# 64 works.

import rtmidi, time, sys, time
import RPi.GPIO as gpio
from collections import namedtuple

MIDI_CHANNEL = 0
assert 0 <= MIDI_CHANNEL <= 0xF

PinInfo = namedtuple("PinInfo", "midi led")

PINS = { # GPIO number -> MIDI controller number
	5: PinInfo(40, 25),
	6: PinInfo(41, 8),
	13: PinInfo(42, 7),
	19: PinInfo(43, 1),
#	26: 44,
}
1,7,8,25

# TODO: have different default values for each pedal
# TODO: maybe have buttons that set all options at once, e.g. to toggle between dirty and clean
state = { k : True for k in PINS.keys() }
midi_out = None

def toggle(pin: int) -> None:
	global state
	controller = PINS[pin].midi
	assert midi_out is not None
	assert 0 <= controller <= 127
	buf = [ 0xB0 | MIDI_CHANNEL, controller, 64 if state[pin] else 0x00 ]
	gpio.output(PINS[pin].led, int(state[pin]))
	print(f"{buf}    led {PINS[pin].led} = {int(state[pin])}")
	midi_out.send_message(buf)
	
	state[pin] = not state[pin]

def setup_gpio() -> None:
	global state
	gpio.setmode(gpio.BCM)
	gpio.setup(16, gpio.OUT)
	for pin in PINS.keys():
		gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
		gpio.setup(PINS[pin].led, gpio.OUT)
		gpio.output(PINS[pin].led, 0)

		# TODO: This is picking up false positives. Set it up so it needs to receive a rising edge,
		# and then *stay* high for at least 50ms.
		# But first identify where the short circuit or loose wire is, because this signal gets sent when I bump the wires.
		#
		# Unrelated: for the final wiring, each LED needs its own resistor. They're too bright without one, and too dim
		# if they're all on the far end of the same one (They probably need fewer ohms each, as well).
		gpio.add_event_detect(pin, gpio.FALLING, callback=toggle, bouncetime=200)

	for k in PINS.keys():
		state[k] = not state # Lets us initialize state with the desired values instead of inverse
		toggle(k)

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
	print("ready")
	sys.stderr.write("ready\n")
	sys.stderr.flush();
	while True:
		time.sleep(200)
except KeyboardInterrupt:
	gpio.cleanup()
	if midi_out:
		midi_out.delete()
		del midi_out

