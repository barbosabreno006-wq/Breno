import json, re
from script_frases import FRASES
d=json.load(open("segs.json")); segs=d["segs"]; N=len(FRASES); M=len(segs)
chars=[len(re.sub(r"\W","",f)) for f in FRASES]
speech=sum(e-s for s,e in segs); k=speech/sum(chars)
INF=1e18
# dp[i][j]: primeiras i frases usam primeiros j segmentos
dp=[[INF]*(M+1) for _ in range(N+1)]; bp=[[0]*(M+1) for _ in range(N+1)]; dp[0][0]=0
for i in range(1,N+1):
    for j in range(i,M+1):
        for m in range(1,min(4,j-i+2)):   # frase usa de 1 a 3 segmentos
            p=j-m
            if dp[i-1][p]>=INF: continue
            dd=segs[j-1][1]-segs[p][0]
            c=dp[i-1][p]+(dd-chars[i-1]*k)**2/(chars[i-1]*k+0.3)
            if c<dp[i][j]: dp[i][j]=c; bp[i][j]=p
j=M; groups=[]
for i in range(N,0,-1):
    p=bp[i][j]; groups.append((p,j)); j=p
groups.reverse()
out=[]
for i,(p,q) in enumerate(groups):
    s=segs[p][0]; e=segs[q-1][1]
    out.append({"i":i+1,"text":FRASES[i],"start":s,"end":e,"nseg":q-p})
    print(f"{i+1:2d} {s:6.2f}-{e:6.2f} ({e-s:4.1f}s, {chars[i]:2d}c, {(e-s)/chars[i]:.3f}s/c, seg={q-p}) {FRASES[i][:44]}")
json.dump(out,open("frases_t.json","w"),ensure_ascii=False)
