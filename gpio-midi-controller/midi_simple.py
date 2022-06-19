# TODO: Put this on github

import rtmidi, time, getch

MIDI_CHANNEL = 0
assert 0 <= MIDI_CHANNEL <= 0xF

def midi_test() -> None:
	midi_out = rtmidi.MidiOut()
	midi_out.open_virtual_port("rdk")

	# midi controller message
	def msg(controller: int, val: int) -> None:
		assert 0 <= controller <= 127
		assert 0 <= val <= 127
		buf = [ 0xB0 | MIDI_CHANNEL , controller, val ]
		print(buf)
		midi_out.send_message(buf)
	with midi_out:
		while True:
			key = getch.getch()
			print(key)
			if '0' <= key <= '9':
				#for i in range(0, 127):
				k = ord(key) - ord('0')
				#v = k % 2
				#k = int(k / 2)
				msg(40 + k, 0)
				#	time.sleep(1)

				# For booleans, just do high half or low half, so 0 or 127 in practice
			elif '>' == key:
				a = [ int(a) for a in input().strip().split() ]
				msg(a[0], a[1])
			elif 'q' == key:
				break
	del midi_out

try:
	midi_test()
except KeyboardInterrupt:
	pass

