#!/bin/awk -f

BEGIN {

    OFS = "";
    MPD_CMD = "mpc";
    MPD_CMD | getline;
    MPD_CMD | getline;
    mpd_state = $1;
    close(MPD_CMD);

part1 = "${voffset 4}${color0}${font Webdings:size=14}"
part2 = "${font}${color}   Song: $alignr$mpd_artist\n${voffset 6}$alignr$mpd_title\n${voffset -4}${color0}${font Martin Vogel's Symbols:size=16}U${font}${color}    Elapsed:\n${voffset 4}$mpd_elapsed/$mpd_length $alignr${color2}${mpd_bar 8,120}${color}"

    if ( mpd_state == "[playing]" )
        print part1, "4", part2
    else {
        if ( mpd_state == "[paused]" )
            print part1, ";",part2;
    }

}
