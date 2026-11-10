# Análise dos vídeos virais (estilo "@aprendendocomvitinho")

Analisei os 3 vídeos frame a frame: contact sheets com 1 frame a cada 3s e trechos com 5 frames/s.
Também medi automaticamente os cortes de cena.

| Vídeo | Duração | Cortes detectados | Média por plano |
|---|---|---|---|
| 1 – "O chão guarda os dias" (praça/pá) | 2:59 | 81 | **~2,2 s** |
| 2 – "Ônibus 47 / seu Valdir" | 2:28 | 97 | **~1,5 s** |
| 3 – "Casa das Trocas" (voz/olhos) | 2:30 | 89 | **~1,7 s** |

> Um detalhe importante: **não é 3D**. É animação **2D vetorial flat no estilo "cutout"**: os bonecos são
> montados com peças (cabeça, tronco, braços em cápsula), com contorno grosso e cores chapadas. A
> sensação de "3D" vem de sombras suaves, profundidade de campo (fundo desfocado), vinheta e movimentos de câmera.

---

## 1. A fórmula da história (o que realmente viraliza)

Os três seguem **o mesmo esqueleto**:

1. **Gancho com regra mágica (0–5s)**: uma regra fantástica dita como fato.
   - "Nesta cidade, o chão guarda todos os dias que já passaram…"
   - "Na Casa das Trocas, você pode trocar qualquer coisa sua…"
   - "O ônibus 47 há 40 anos…"
2. **Narrador em 1ª pessoa, criança ou idoso**, que conta "a minha história".
3. **Vida comum com detalhes concretos**: nomes (Valdir, Cida), números ("6 anos", "40 passageiros", "63 anos atrás"), horários ("6h30").
4. **Passagem do tempo em montagem rápida**: crianças → casamento → filhos → velhice (vídeo 1, 1:09–2:03).
5. **Perda ou sacrifício**: alguém morre, se aposenta, troca algo precioso.
6. **Reviravolta emocional (twist)** nos últimos 30–40s, ligando o começo ao fim:
   - o velho cava o dia em que conheceu a esposa e descobre que *ele* era o "idiota que deixou cair a pipoca";
   - todos os passageiros que ele ajudou esperam no ponto final com cartazes;
   - a "voz" que o menino trocou era a da mãe.
7. **Fecho com lágrimas + frase de impacto** (close no rosto chorando, vinheta escura).

Duração: **2:30–3:00** (retenção alta porque a história só se resolve no final).

## 2. Linguagem visual

- **Formato**: 9:16, 576×1024 (publicar em 1080×1920), 30 fps.
- **Personagens**: cabeça enorme (≈40% do corpo), olhos grandes com brilho branco, bochechas rosadas,
  braços em "salsicha", contorno escuro grosso (~6–8 px).
- **Paleta**: tons pastel quentes; cenas tristes ficam **dessaturadas / azuladas**; memórias felizes
  ficam **saturadas e douradas**. A cor conta a emoção.
- **Fundo**: casinhas coloridas, praças, interior de ônibus; muitas vezes **desfocado** quando há close.
- **Objeto-símbolo recorrente**: a pá dourada, o ônibus 47, os potes com etiqueta. Ele aparece no começo,
  no meio e no clímax.

## 3. Como as animações funcionam (frame a frame)

Vistos a 5 fps, os movimentos são simples. O vídeo parece "vivo" porque eles se sobrepõem:

| Técnica | Como aparece | Onde vi |
|---|---|---|
| **Idle/respiração** | o boneco sobe e desce 2–4 px, com squash & stretch leve | todos os planos |
| **Troca de pose** | o braço salta de posição em 2–3 frames (acenar, cavar, apontar) | v2 0:02, v1 0:03 |
| **Troca de expressão** | os olhos/boca são trocados (feliz → choro com lágrimas em gotas) | v2 0:04 |
| **Piscar** | 2–3 frames com o olho fechado a cada ~3s | geral |
| **Push-in lento (Ken Burns)** | zoom de 1.0 a ~1.15 ao longo do plano | aberturas |
| **Punch-in** | zoom rápido (≈0,3s) no rosto para impacto/surpresa | v1 0:30, v2 0:42 |
| **Whip-pan** | a tela "chicoteia" na horizontal com **motion blur** forte por 6–8 frames | v1 0:00–0:02 |
| **Zoom/blur entre mundos** | dissolve + desfoque radial para memórias e "viagem no tempo" | v1 0:51, v3 1:39 |
| **Balão de pensamento** | círculo branco com uma mini-cena dentro, entra com pop | v1 0:03, 2:12 |
| **Partículas** | brilhos, poeira dourada, chuva, gotas de lágrima | clímax |
| **Onomatopeia/ícones** | "?", setas, "TOC TOC", números gigantes (2, 1) | v2 1:06 |
| **Vinheta** | bordas escurecidas, mais fortes no final emocional | finais |

## 4. Legenda e áudio

- **Legenda karaokê**: blocos de 2–4 palavras, fonte sans **extra-bold** (estilo Poppins/Montserrat),
  **branca com contorno preto**, e **a palavra falada em amarelo** (às vezes vermelho em palavras fortes:
  "idiota", "odiava"). Fica centralizada em ~80% da altura.
- **Narração**: voz calma, pausada, provavelmente **IA/TTS** (o vídeo 3 até mostra "voz de IA").
- **Trilha**: piano/cordas emocional, crescendo no clímax. **SFX** em cada ação: whoosh no whip, pop,
  batida, brilho.

## 5. Pipeline recomendado para produzirmos

1. **Roteiro** (300–420 palavras ≈ 2:30): gancho mágico → vida → tempo → perda → twist → frase final.
2. **Narração**: ElevenLabs / CapCut TTS em pt-BR, ritmo ~150 palavras/min.
3. **Storyboard**: 1 plano a cada frase curta (~1,5–2,2 s) → 70–100 planos.
4. **Arte**: personagens em peças separadas (cabeça, olhos, boca, braços) – Illustrator / Affinity /
   Canva; ou gerar com IA e recortar.
5. **Animação**: CapCut, After Effects (Duik/Joysticks), Moho, Cartoon Animator, **ou o nosso
   gerador por código** (`gerar_video.py`), que já faz idle, piscar, câmera, whip, legenda e trilha.
6. **Legenda**: legenda automática do CapCut com destaque da palavra (template "karaokê" amarelo).
7. **Finalização**: vinheta, música a −18 dB sob a voz, SFX, export 1080×1920 30 fps.

## 6. Nosso vídeo: "A Vela da Dona Cida" (história original)

O demo gerado (`demo_vela_dona_cida.mp4`, ~32s) é a **abertura/Parte 1** e serve de prova do estilo.
Roteiro completo para a versão de ~2:30:

> **Gancho** — Na minha rua, toda janela tem uma vela acesa. Ela só fica acesa enquanto alguém lembra de você.
> Mas uma janela vivia apagada: a da Dona Cida. Ninguém visitava ela há vinte anos.
>
> **Ação** — Num domingo, eu pensei nela o dia inteiro. Então eu fui lá e bati na porta. Ela me olhou como se
> tivesse visto um fantasma. Naquela tarde a gente riu tanto que a vela dela acendeu.
>
> **Vida** — Eu comecei a ir todo domingo. Ela me ensinou a fazer bolo de fubá, a soltar pipa, a perder no
> dominó sem chorar. A vela dela era a mais forte da rua.
>
> **Tempo** — Eu cresci. Fui pra faculdade em outra cidade. Os domingos viraram ligações… depois mensagens…
> depois nada.
>
> **Perda** — Um dia minha mãe ligou: "A vela da Dona Cida está fraquinha."
> Eu peguei o primeiro ônibus. Quando cheguei, a janela estava escura.
>
> **Twist** — Em cima da mesa tinha uma caixa com meu nome. Dentro, uma vela pequena e um bilhete:
> "Essa é a sua. Ela ficou acesa todos esses anos porque eu nunca parei de lembrar de você."
> Foi aí que eu entendi: durante vinte anos, a vela que ninguém via apagar… era a minha.
>
> **Fecho** — Hoje eu visito alguém todo domingo. Porque tem gente que só precisa de uma batida na porta.

**Planos-chave do twist**: close da caixa (punch-in), mão abrindo, bilhete com a letra dela, flashback rápido
em montagem (bolo, pipa, dominó) com zoom-blur, a vela pequena acendendo na mão dele, pull-out para a rua
inteira iluminada, close chorando com vinheta.
