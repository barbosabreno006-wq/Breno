#!/bin/bash
cd /home/user/Breno/video
N=$(python3 -c "import render;print(int(render.TOTAL*30)+1)")
echo frames $N
rm -f part*.mp4
Q=$(( (N+3)/4 ))
for i in 0 1 2 3; do a=$((i*Q)); b=$(( (i+1)*Q )); [ $b -gt $N ] && b=$N; python3 render.py chunk $a $b part$i.mp4 & done
wait
printf "file 'part0.mp4'\nfile 'part1.mp4'\nfile 'part2.mp4'\nfile 'part3.mp4'\n" > parts.txt
ffmpeg -v error -y -f concat -safe 0 -i parts.txt -c copy video_mudo.mp4
ffmpeg -v error -y -i video_mudo.mp4 -i voz.mp3 -filter_complex "[1:a]apad[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest piscinas.mp4
echo done
