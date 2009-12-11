#!/usr/bin/env python
import sys
import os
import subprocess

# root filesystem
statb = subprocess.Popen("stat -f -c %b /", shell=True, stdout=subprocess.PIPE,)
statb_value = statb.communicate()[0]
statf = subprocess.Popen("stat -f -c %f /", shell=True, stdout=subprocess.PIPE,)
statf_value = statf.communicate()[0]
total = int(statb_value)
used = total - int(statf_value)
dec = (((used * 100) / total) + 5) / 10
if dec > 9:
	icon = "0"
elif dec < 1:
	icon = "A"
else:
	icon = str(dec)
print "${voffset 3}${color0}${font Pie charts for maps:size=15}"+icon+"${font}${color}   ${voffset -9}Root: ${font Liberation Sans:style=Bold:size=8}${color1}${fs_free_perc /}%${color}${font}"
print "${offset 29}F:${color2}${fs_free /}${color} U:${color2}${fs_used /}${color}"

# /home folder (if its a separate mount point)
if os.path.ismount("/home"):
	# start calculation for the pie chart symbol (icon)
	statb = subprocess.Popen("stat -f -c %b /home", shell=True, stdout=subprocess.PIPE,)
	statb_value = statb.communicate()[0]
	statf = subprocess.Popen("stat -f -c %f /home", shell=True, stdout=subprocess.PIPE,)
	statf_value = statf.communicate()[0]
	total = int(statb_value)
	used = total - int(statf_value)
	dec = (((used * 100) / total) + 5) / 10
	if dec > 9:
		icon = "0"
	elif dec < 1:
		icon = "A"
	else:
		icon = str(dec)
	# end calculation icon
	print "${voffset 2}${color0}${font Pie charts for maps:size=15}"+icon+"${font}${color}   ${voffset -9}Home: ${font Liberation Sans:style=Bold:size=8}${color1}${fs_free_perc /home}%${color}${font}"
	print "${offset 29}F:${color2}${fs_free /home}${color} U:${color2}${fs_used /home}${color}"

# folder in /media
for device in os.listdir("/media/"):
	if (not device.startswith("cdrom")) and (os.path.ismount('/media/'+device)):
		# start calculation dec value (for the pie chart symbol)
		statb = subprocess.Popen('stat -f -c %b "/media/'+device+'"', shell=True, stdout=subprocess.PIPE,)
		statb_value = statb.communicate()[0]
		statf = subprocess.Popen('stat -f -c %f "/media/'+device+'"', shell=True, stdout=subprocess.PIPE,)
		statf_value = statf.communicate()[0]
		total = int(statb_value)
		used = total - int(statf_value)
		dec = (((used * 100) / total) + 5) / 10
		if dec > 9:
			icon = "0"
		elif dec < 1:
			icon = "A"
		else:
			icon = str(dec)
		# end calculation dec
		print "${voffset 2}${color0}${font Pie charts for maps:size=15}"+icon+"${font}${color}   ${voffset -9}"+device.capitalize()+": ${font Liberation Sans:style=Bold:size=8}${color1}${fs_free_perc /media/"+device+"}%${color}${font}"
		print "${offset 29}F:${color2}${fs_free /media/"+device+"}${color} U:${color2}${fs_used /media/"+device+"}${color}"
