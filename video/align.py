import subprocess, re, json
from script_frases import FRASES
a = subprocess.run(["ffmpeg","-hide_banner","-i","voz.mp3","-af","silencedetect=n=-33dB:d=0.1","-f","null","-"],capture_output=True,text=True).stderr
dur = float(re.search(r"Duration: (\d+):(\d+):([\d.]+)",a).group(1))*3600+float(re.search(r"Duration: (\d+):(\d+):([\d.]+)",a).group(2))*60+float(re.search(r"Duration: (\d+):(\d+):([\d.]+)",a).group(3))
st=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",a)]
en=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",a)]
segs=[]; cur=0.0
for s,e in zip(st,en):
    if s-cur>0.15: segs.append((cur,s))
    cur=e
if dur-cur>0.15: segs.append((cur,dur))
print("duração",dur,"segmentos",len(segs),"frases",len(FRASES))
json.dump({"dur":dur,"segs":segs},open("segs.json","w"))
