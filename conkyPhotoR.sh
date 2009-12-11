#Source Code follows
source="/home/helmuth/Imagens/Beauty/"
photo=~/.conkyPhoto.png

cd $source
number=$(ls | wc -l)
random=$RANDOM
random=${random}%${number}
lines=`echo ${random} + 2 | bc`
filename=`ls | head -n $lines | tail -n 1`

	cp $filename $photo

	picture_aspect=$(($(identify -format %w $photo) - $(identify -format %h $photo)))

	if [ "$picture_aspect" = "0" ]; then
		convert $photo  -thumbnail 250x250 $photo
	elif [ "$picture_aspect" -gt "0" ]; then
		convert $photo  -thumbnail 300x250 $photo
		convert $photo -crop 250x250+$(( ($(identify -format %w $photo) - 250) / 2))+0  +repage $photo
	else
		convert $photo  -thumbnail 250x500 $photo
		convert $photo -crop 250x250+0+$(( ($(identify -format %h $photo) - 250) / 2))  +repage $photo
	fi

	# Theme 1
	#convert $photo  \( +clone  -threshold -1 -draw 'fill black polygon 0,0 0,10 10,0 fill white circle 10,10 10,0' \( +clone -flip \) -compose Multiply -composite \( +clone -flop \) -compose Multiply -composite \) +matte -compose CopyOpacity -composite $photo
	#convert -page +4+4 $photo -matte \( +clone -background black  -shadow 60x3+0+0 \) +swap -background none -mosaic $photo

	# Theme 2
	convert $photo -bordercolor black -border 6 -background  none -rotate 4 -background black  \( +clone -shadow 50x4+4+4 \) +swap -background none -flatten $photo

exit 0

