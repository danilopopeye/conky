#!/bin/bash
# conkyHDDtemp.sh
# by helmuthdu

HDDtemp="hddtemp -n /dev/sda"

if [ "$HDDtemp" < 40 ]; then
	echo "cool"
elif [ "$HDDtemp" > 55 ]; then
	echo "hot"
else
	echo "warm"
fi

exit 0
