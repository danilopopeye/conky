#!/usr/bin/env python
#created by iggykoopa
 
import os

rate = 0.0
batteries = os.listdir("/proc/acpi/battery")
if batteries:
    batInfo = open("/proc/acpi/battery/%s/state" % (batteries[0],))
    voltage = 0.0
    watts_drawn = 0.0
    amperes_drawn = 0.0
    available = True
    for line in batInfo:
        if "charging state" in line:
            if not "discharging" in line:
                available = False
        if "present voltage" in line:
            voltage = float(line.split()[2]) / 1000.0
        if "present rate" in line and "mW" in line:
            watts_drawn = float(line.split()[2]) / 1000.0
        if "present rate" in line and "mA" in line:
            amperes_drawn = float(line.split()[2]) / 1000.0
    rate = watts_drawn + voltage * amperes_drawn
    if available:
        print rate
    else:
        print "No Power"
else:
    print "No Power" 
