# Audio — HeyGen hudba + HRAVÉ SFX + ducking

**Řeší opakovaný feedback: zvuk musí být HRAVÝ a živý, ne technický.** Zdroj = HeyGen 250k+ knihovna (`scripts/heygen_audio.py`), NE FAL. Naše převaha — Sařino repo audio vrstvu nemá.

## Princip (technické vs hravé)

| Technické (❌) | Hravé (✅) |
|---|---|
| FAL generovaná mlha, ostré cvaky/šum | charakterní pojmenované zvuky (Heart Pop, Single Boing, Sparkle, Swipe whoosh) |
| zvuk na každém prvku | řídké akcenty jen na hero beatech (0.4–0.6/s) |
| SFX sólo, plochá hlasitost | hudební podlaha + SFX špičky, punch na beatu, klid mezi |

## Hledání a stažení (heygen_audio.py)

```bash
# prozkoumat (zdarma, žádný download):
python3 scripts/heygen_audio.py search --query "playful bouncy UI pop, soft round" --type sfx
python3 scripts/heygen_audio.py search --query "dark premium tech, cinematic, 100 bpm" --type music
# stáhnout + zpracovat:
python3 scripts/heygen_audio.py get --query "soft whoosh swipe" --type sfx --pick 0 --out <proj>/assets/sfx/whoosh.mp3
python3 scripts/heygen_audio.py get --query "..." --type music --name "Astral..." --out <proj>/assets/music.mp3 --duration 35
```
Hledá se **popisem charakteru**, ne technicky. SFX se normalizuje (limiter −3 dB), hudba ořízne na `--duration` + fade.

## Hravá paleta (ověřené HeyGen kusy)

| Kategorie | HeyGen názvy | Kam (recept zvuk→pohyb) |
|---|---|---|
| **Pop** | Heart Pop, Soft UI Pop, Standard Pop | kaskáda/fan-out/drop/chip |
| **Boing** | Single Boing, Funny Boing Wobble | spring (back.out) vstup, bounce dopad |
| **Sparkle** | Sparkle, Magic, Reveal logo | reveal hero, „generuji" |
| **Whoosh** | Swipe whoosh, Swoosh 2, Whoosh | nástup scény, transition |
| **Click** | Quick Toggle Switch, Sharp Switch Flip | toggle/send/satisfying moment |
| **Bell** | Chime, Single Bell Strike | count-up tečka, jemný outro |

## Mix profil (cíl — ověř spolehlivě, viz „Ověření zvuku" níže)

- Hudba podlaha `data-volume` ~0.55, celé video. SFX akcent peak **−2…−4 dB**. Klid mezi (jen hudba) **−12…−16 dB**. Konec do ticha (poslední 10 % nejtišší, žádná fanfára).
- Každý překrývající se zvuk = vlastní `data-track-index` (hudba 2, SFX 3+).
- ⚠️ 3 SFX blízko u sebe se sčítají → rozestup +0.05s nebo −1 dB, ať nepřebijí.

## Hudba (podlaha)

`--type music`, vibe = music brief stylu (z `frame.md`). Stopy jsou 5–43s úseky → `--duration` ořízne + fade. Po stažení ověř BPM poslechem prvních beatů vs grid; nesedí → levnější regenerovat než přečasovat.

## Ducking (hudba pod hlasem — jen u VO videí)

Sidechain compress (Sara, ověřené):
```
[bed][narrside]sidechaincompress=threshold=0.028:ratio=4:attack=18:release=260[ducked];
[narr][ducked]amix=inputs=2:duration=first,alimiter=limit=0.95[a]
```
Volume strategie: hook hlasitější → narrace tišší → hustá pasáž ještě tišší (nepumpuj zpět v krátkých pauzách) → CTA může vystoupit a doznít. ⚠️ „Hudba ve streamu, ale neslyšitelná" je pojmenovaná chyba — kontroluj slyšitelnost, ne jen přítomnost stopy.

## Per-styl charakter

- **Playful Pop:** boings + marimba/bell, víc akcentů. **Dark Premium (CliqSales):** měkké popy + sparkle střídmě, toggle clicky, dark synth hudba (hravé, ale prémiové). **Elegant SaaS:** chimes + soft whoosh, řídké. **Light Editorial:** typing + soft pop + warm chime.

## Fade in/out (povinné, ať to neutne)

Pavlův feedback: hudba nesmí nastoupit zhurta ani být na konci utnutá.
- **Fade in** hudby ~1 s na začátku — ale **jen na music bus** (před mixem s VO), ať není dotčený úvodní hlas: `[mus]…,volume=…,afade=t=in:st=0:d=1.1`.
- **Fade out** konce do ztracena. ⚠️ `loudnorm` je dynamický a fade-out **po něm tahá zpět nahoru** (vypadá, že fade nefunguje) → fade out dělej **druhým průchodem**: pass 1 = mix + `loudnorm` → temp MP4; pass 2 = `ffmpeg -i temp -af "afade=t=out:st=<konec−1.1>:d=1.1" -c:v copy final.mp4`.

## Ověření zvuku (NE `volumedetect`/`astats Overall` — KLAMOU)

Pojmenovaná past: `astats …Overall.RMS_level` je **kumulativní** (ne po oknech) a `volumedetect` grep ze stderru často nic nevrátí → obálku/fade/fade-out NEUKÁŽOU (vypadá ploše, i když fade reálně je). Spolehlivě:
- **Obálka / fade (in i out):** dekóduj do mono WAV (`ffmpeg -i final.mp4 -ac 1 -ar 16000 -c:a pcm_s16le x.wav`) a spočítej RMS po 0,2 s oknech v Pythonu přes stdlib `wave` (žádné numpy). Fade in = roste z ~−40 dB; fade out = klesá k ~−50 dB.
- **Timing SFX:** postav **SFX-only** stopu (jen efekty, bez hudby/VO) a pusť `silencedetect=noise=-45dB:d=0.08` → vypíše přesné start/end každého cinkance; porovnej se zamýšlenými časy.

## Zákazy

❌ FAL SFX · ❌ ostré technické cvaky · ❌ SFX na každém prvku · ❌ SFX bez hudby · ❌ hlasitý konec · ❌ ověřování fade přes `volumedetect`/`astats Overall`.
