#!/bin/env python3

# NOTE: Seems to work for the dirty bank but not clean?
# dirty *doesn't* have the checkmark in the midi setup dialog box
# Yep, that's what did it.

# NOTE: Don't use 0xFF for the "on" message value. Seems to be a magic number
# of some kind; jack's midi monitor program prints it differently.
# 64 works.

import rtmidi, time
import RPi.GPIO as gpio

MIDI_CHANNEL = 0
assert 0 <= MIDI_CHANNEL <= 0xF

PINS = { # GPIO number -> MIDI controller number
	5: 40,
	6: 41,
	13: 42,
	19: 43,
	26: 44,
}

# TODO: have different default values for each pedal
# TODO: maybe have buttons that set all options at once, e.g. to toggle between dirty and clean
state = { k : True for k in PINS.keys() }
midi_out = None

def toggle(pin: int) -> None:
	global state
	controller = PINS[pin]
	assert midi_out is not None
	assert 0 <= controller <= 127
	buf = [ 0xB0 | MIDI_CHANNEL, controller, 64 if state[pin] else 0x00 ]
	state[pin] = not state[pin]
	print(buf)
	midi_out.send_message(buf)

def setup_gpio() -> None:
	global state
	gpio.setmode(gpio.BCM)
	gpio.setup(16, gpio.OUT)
	for pin in PINS.keys():
		gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
		gpio.add_event_detect(pin, gpio.FALLING, callback=toggle, bouncetime=500)

	for k in PINS.keys():
		state[k] = not state # Lets us initialize state with the desired values instead of inverse
		toggle(k)

def setup_midi() -> None:
	global midi_out
	midi_out = rtmidi.MidiOut()
	midi_out.open_virtual_port("gpio")

try:
	setup_midi()
	setup_gpio()
	while True:
		time.sleep(20)
except KeyboardInterrupt:
	gpio.cleanup()
	if midi_out:
		midi_out.delete()
		del midi_out

