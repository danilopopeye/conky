#!/bin/bash
#
# Album art with cd theme in conky
# by helmuthdu

player="`python ~/.conky/conkyBanshee.py --datatype=CA | sed -e 's/\\\//g'`"
cover="/tmp/conkyCover.png"

picture_aspect=$(($(identify -format %w "$cover") - $(identify -format %h "$cover")))

if [ ! -f "$player" ]; then
	convert ~/.conky/CD/base.png ~/.conky/CD/top.png -geometry +0+0 -composite "$cover"
else
	cp "$player" "$cover"
	if [ "$picture_aspect" = "0" ]; then
		convert "$cover"  -thumbnail 98x98 "$cover"
	elif [ "$picture_aspect" -gt "0" ]; then
		convert "$cover"  -thumbnail 300x98 "$cover"
		convert "$cover" -crop 98x98+$(( ($(identify -format %w "$cover") - 86) / 2))+0  +repage "$cover"
	else
		convert "$cover"  -thumbnail 98x500 "$cover"
		convert "$cover" -crop 98x98+0+$(( ($(identify -format %h "$cover") - 86) / 2))  +repage "$cover"
	fi
	convert ~/.conky/CD/base.png "$cover" -geometry +19+5 -composite ~/.conky/CD/top.png -geometry +0+0 -composite "$cover"
fi

exit 0
