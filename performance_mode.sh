#!/bin/bash
echo -n performance | sudo tee  /sys/devices/system/cpu/cpu{0,1,2,3}/cpufreq/scaling_governor
