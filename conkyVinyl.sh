#!/bin/bash
#
# Album art with cd theme in conky
# by helmuthdu

player="`python ~/.conky/conkyBanshee.py --datatype=CA | sed -e 's/\\\//g'`"
cover="/tmp/conkyCover.png"

picture_aspect=$(($(identify -format %w "$cover") - $(identify -format %h "$cover")))

if [ ! -f "$player" ]; then
	convert ~/.conky/Vinyl/base.png ~/.conky/Vinyl/top.png -geometry +0+0 -composite "$cover"
else
	cp "$player" "$cover"
	if [ "$picture_aspect" = "0" ]; then
		convert "$cover"  -thumbnail 86x86 "$cover"
	elif [ "$picture_aspect" -gt "0" ]; then
		convert "$cover"  -thumbnail 300x86 "$cover"
		convert "$cover" -crop 86x86+$(( ($(identify -format %w "$cover") - 86) / 2))+0  +repage "$cover"
	else
		convert "$cover"  -thumbnail 86x500 "$cover"
		convert "$cover" -crop 86x86+0+$(( ($(identify -format %h "$cover") - 86) / 2))  +repage "$cover"
	fi
	convert ~/.conky/Vinyl/base.png "$cover" -geometry +4+3 -composite ~/.conky/Vinyl/top.png -geometry +0+0 -composite "$cover"
fi

exit 0

