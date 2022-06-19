#!/bin/bash
echo -n performance | sudo tee  /sys/devices/system/cpu/cpu{0,1,2,3}/cpufreq/scaling_governor
#/usr/bin/jackd -P9 -dalsa -r192000 -p128 -n3 -D -Chw:USB -Phw:USB
#a2jmidid -e # probably needs to start *after* jack. Lets midi.py talk to jackd
sleep 1
guitarix
echo -n ondemand | sudo tee  /sys/devices/system/cpu/cpu{0,1,2,3}/cpufreq/scaling_governor
