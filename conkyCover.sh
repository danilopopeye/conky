#!/bin/bash
#
# Album art with cd theme in conky
# by helmuthdu

# player="`python ~/.conky/conkyRhythmbox.py --datatype=CA | sed 's/[%20 ]\+/\\ /g'`"
player="`python /usr/share/conkyrhythmbox/conkyRhythmbox.py --datatype=CA | sed 's/[%20 ]\+/\\ /g'`"
icon=~/.conky/Players/rhythmbox.png
cover=/tmp/conkyCover.png

if [ ! -f "$player" ]; then
	# cp $icon $cover
	convert ~/.conky/CD/base.png ~/.conky/CD/top.png -geometry +0+0 -composite $cover
else
	convert "$player" -thumbnail 98x98 $cover
	convert ~/.conky/CD/base.png $cover -geometry +19+5 -composite ~/.conky/CD/top.png -geometry +0+0 -composite $cover
fi

exit 0
