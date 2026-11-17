import json, re
from script_frases import FRASES
segs=json.load(open("segs.json"))["segs"]; M=len(segs)
toks=[]  # (palavra, quebra_depois)
for fi,f in enumerate(FRASES):
    ws=f.split()
    for wi,w in enumerate(ws):
        toks.append({"w":w,"f":fi+1,"brk":(wi==len(ws)-1) or w.endswith(",")  ,"end":wi==len(ws)-1})
T=len(toks); SPOK={"R$200":15,"R$500":16,"R$15":10,"R$250":23,"R$1.000":9,"R$5.000":15,"R$60":9,"pH":6,"Pix":4}
wt=[SPOK.get(t["w"].strip(","),len(re.sub(r"\W","",t["w"])))+1.5 for t in toks]
cum=[0]
for x in wt: cum.append(cum[-1]+x)
speech=sum(e-s for s,e in segs); k=speech/cum[-1]
INF=1e18
dp=[[INF]*(T+1) for _ in range(M+1)]; bp=[[0]*(T+1) for _ in range(M+1)]; dp[0][0]=0
for j in range(1,M+1):
    d=segs[j-1][1]-segs[j-1][0]
    for b in range(j,T+1):
        pen=0 if (toks[b-1]["brk"] or b==T) else 6.0
        for a in range(max(0,b-30),b):
            if dp[j-1][a]>=INF: continue
            exp=k*(cum[b]-cum[a])
            c=dp[j-1][a]+((d-exp)**2)/(exp+0.15)*4+pen
            if c<dp[j][b]: dp[j][b]=c; bp[j][b]=a
b=T; runs=[]
for j in range(M,0,-1):
    a=bp[j][b]; runs.append((a,b)); b=a
runs.reverse()
words=[]
for j,(a,b) in enumerate(runs):
    s,e=segs[j]; d=e-s; tot=cum[b]-cum[a]; t=s
    txt=" ".join(toks[i]["w"] for i in range(a,b))
    print(f"seg{j:2d} {s:6.2f}-{e:6.2f} {d:4.1f}s {d/tot/k:4.2f}x  {txt[:70]}")
    for i in range(a,b):
        dd=d*wt[i]/tot
        words.append({"w":toks[i]["w"],"f":toks[i]["f"],"s":t,"e":t+dd*0.97,"end":toks[i]["end"]}); t+=dd
json.dump(words,open("words.json","w"),ensure_ascii=False)
