# Voiceover — Gemini 3.1 Flash TTS (český VO pro video)

Pravidla pro **volitelný** český voiceover přes FAL `fal-ai/gemini-3.1-flash-tts`. VO není povinný — některá videa jedou jen na hudbě + SFX. Když VO je, **řídí timing celého videa** (scény se časují na jeho segmenty).

## Workflow (text v Kroku 2, audio v Kroku 3.5 — PŘED stavbou scén)

1. **Napiš script** v **Kroku 2** (storyboard) — nebo nabídni 1–5 variant podle úhlu příběhu. VO copy = **vykání**, brand hlas (viz brandDNA). Schválí se na STOP 2.
2. V **Kroku 3.5** se **zeptej na pohlaví hlasu** („Mužský nebo ženský?") → default preset.
3. **Vygeneruj 2–3 varianty hlasů** (různé presety) → `open` je uživateli na porovnání → vybere.
4. Finál ulož jako `assets/audio/voiceover.mp3`, **změř délku** (`ffprobe`) → timing master; podle něj se časují scény v Kroku 4.

## Voice presets (Gemini)

| Voice | Vibe | Použití |
|-------|------|---------|
| **Aoede** | Warm, female, mid-30s, intimate | Premium wellness, beauty (female default) |
| **Callirrhoe** | Female, calm, slightly older | Mature, autoritní |
| **Sulafat** | Female, brighter, younger | Lifestyle, mladší cílovka |
| **Kore** | Female, neutral newsy | Informativní, educational |
| **Charon** | Male, deep, authoritative | Tech, B2B, finance (male default) |
| **Algieba** | Male, warmer, conversational | Testimonial, friendly brands |
| **Enceladus** | Male, charakterní, hluboký + hravý | **Produkčně osvědčený** pro explainer s emocí |
| **Puck** / **Fenrir** | Male, upbeat / energetic | Hravé, energické |

Další: `Achernar`, `Algenib`, `Achird`, `Alnilam`, `Autonoe`, `Despina`, `Erinome`, `Gacrux`, `Iapetus`, `Laomedeia`, `Leda`, `Orus`, `Pulcherrima`, `Rasalgethi`, `Sadachbia`, `Sadaltager`, `Schedar`, `Umbriel`, `Vindemiatrix`, `Zephyr`, `Zubenelgenubi`. (Full list v Gemini/FAL docs.)

> **Hloubku/hravost laď přes `style_instructions`, ne přes hlas.** Vygeneruj 2–3 a nech vybrat — výběr hlasu je subjektivní.

## Best practices pro `style_instructions`

1. **Continuous flowing, minimal pauses** — bez explicitního „SHORT, minimal pauses, no long gaps" Gemini cpe pauzu po každé tečce a stopáž nabobtná (a zní roboticky).
2. **Graduation arc** — definuj emocionální oblouk po větách (např. „start with empathy on the problem, lift with optimism on the solution, land with pride on the result"). Bez toho čte monotónně.
3. **Tonalita + negativní omezení** — konkrétně („deep, warm, playful, characterful") **+ „NOT a commercial announcer"** (bez toho sklouzne do reklamního podání).
4. **Phonetic respell brand names přímo ve scriptu** (TTS čte přesně co je napsáno): „Aqueena" → „Akvýna", „Zepter" → „Ceptru", „MedAll" → „MedÓl". V `style_instructions` doplň co je co.
5. **Inline emotion tagy** střídmě: `[short pause]`, `[soft laugh]`, `[sigh]`. (Mají přednost před globálním „no pauses".)

## Produkční learningy ⭐

- **Hlubší hlas (trik):** ffmpeg pitch-down `asetrate=24000*0.93,aresample=24000,atempo=1/0.93` — sníží výšku ~7 %, drží tempo. (Gemini default 24 kHz mono.)
- **Glitch-retry:** TTS občas vrátí ~1–2 s (nenamluví celý text). **Vždy zkontroluj `duration`** a při < ~25 s (resp. < očekávané) **retry** (loop max 3×).
- **Queue API, ne sync:** delší VO → `https://queue.fal.run/fal-ai/gemini-3.1-flash-tts` + polling `status_url` do `COMPLETED`, pak `response_url`. Sync `fal.run` na delším textu timeoutuje na read.
- **„Pauzy moc dlouhé" fix bez ztráty interpretace:** přegeneruj se silnějším „SHORT minimal pauses" (ne stříhat ticho ffmpegem — zní useknutě).
- **„Víc hravě/pozitivně + zpomal"** = `style_instructions`: „playful, upbeat, positive, smiling, relaxed pace, NOT rushed, no long silences". (Tempo i hravost jde čistě přes instrukce.)
- **Klíč inline** z `.claude/settings.local.json` (`FAL_KEY`), NIKDY nevypisovat hodnotu.

## VO + zbytek audia

VO se mixuje **až v ffmpeg post-mixu** (HyperFrames renderuje silent). Detaily a sound recipes: `references/audio.md`.
- **VO = hlavní stopa** (vol 1.0, start ~0.5 s po začátku videa).
- **Hudba potichu pod VO** (vol ~0.10–0.12, fade in/out) — žádný sidechain netřeba, jen drž nízko.
- **SFX light** (0.28–0.5) na eventy (psaní/klik/pop/whoosh).
- **Scény časuj na VO segmenty** — po renderu poslechni sync a dolad stopáže scén (viz `assembly.md`).

## Length & timing

- **30 s video** → VO ~26–28 s (+ nájezd/dojezd). **45 s** → ~38–40 s. **60 s** → ~52–55 s.
- Rate ~2.5–3 slova/s. Delší věty = pomalejší, kratší = rytmičtější.
- VO je primární — radši zkrať scénu/script než aby VO přetékalo přes konec.

## Endpoint

```python
endpoint = "fal-ai/gemini-3.1-flash-tts"
arguments = {
    "prompt": script,                          # plný text (s respelly)
    "voice": "Enceladus",
    "style_instructions": style_text,
    "language_code": "Czech (Czech Republic)", # NE "cs" — descriptive jméno
}
# result["audio"]["url"] → stáhni do assets/audio/voiceover.mp3
```

⚠️ `language_code` musí být descriptive (`"Czech (Czech Republic)"`), ISO `"cs"` Gemini odmítne.

## Output & cena

- `documents/videos/<slug>/assets/audio/voiceover.mp3` (MP3, 24 kHz mono).
- Cena ~$0.04 / 1M znaků → prakticky zdarma, **iterace VO jsou levné** (proto klidně 2–3 hlasy na výběr + retry).

## FAL Gemini TTS — 422 a kvóta (learning)

- Některé věty vrací opakovaně **HTTP 422** (často o tvorbě médií — „hlas", „grafika, video, zvuk"). Řešení: **přeformuluj větu** jinými slovy.
- FAL má **malou klouzavou kvótu** na TTS (~1 souběžný request). Mezi segmenty cooldown (12+ s); na 422 při submitu čekej 30–180 s a opakuj. Nikdy neblokuj celý běh kvůli jednomu segmentu — vygeneruj zbytek, chybějící dogeneruj zvlášť.
