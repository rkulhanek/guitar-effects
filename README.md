Control software for a Raspberry Pi-based multi-effects setup for guitar.

In progress.

# Files

## Root directory

* `./create_symlinks.sh` will link the config files for jackd and guitarix to the ones in this repo. Assumes those config files don't already exist.
* `./start.sh` will eventually start all the necessary things running, in the right order, and with all needed delays. Doesn't yet.

## gpio-midi-controller

* `adc.py` talks to the rheostat pedals via the mcp3008
* `midi.py` converts gpio pushbutton signals into midi controller messages that will be received by guitarix

The rest are *probably* not needed anymore.

# TODO
Add wiring diagram
