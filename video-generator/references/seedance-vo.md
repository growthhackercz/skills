# Seedance + český voiceover — ponechaná alternativní cesta

Kdy místo Omni:
- **Nikdo nemluví na kameru** (voiceover přes obraz) — lip-sync není potřeba.
- Potřebuješ **realistický multishot v jedné generaci** (Seedance 2.0 umí až 15 s se shot labels).
- **EN/ES dialog v záběru** → Seedance native (mluví přímo, lip-sync EN/ES OK).

## Pipeline (CZ voiceover)

1. Scény generuj Seedance 2.0 (`bytedance/seedance-2.0/reference-to-video`, ~$0,30/s; fast varianta ~$0,24/s) — **bez dialogu v záběru**, audio jen ambience/silent.
2. Český VO: **Gemini TTS** (`fal-ai/gemini-3.1-flash-tts`, `language_code: "Czech (Czech Republic)"`; mužské hlasy Charon/Algieba/Enceladus). Style instructions: „deep, calm, NOT announcer, continuous flowing, minimal pauses“. Glitch retry (občas vrátí ~1–2 s).
3. VO řídí timing scén — piš VO script před stavbou scén, scény časuj na jeho segmenty.
4. Finishing + mux stejné jako u Omni (`finishing-hyperframes.md`): titulky verbatim dle VO, hudba HeyGen s gradací, ducking.

## Seedance poznámky

- `image_url` musí být **uploaded HTTPS URL** (`fal_client.upload_file_async`) — data URLs odmítá. Async submit (60–180 s generace).
- `generate_audio: False` pro VO cestu (audio se skládá v postu).
- Delší video: 2×15 s two-part s casting-sheet lockem, nebo přejdi na Omni řetězení (konzistence postav je tam silnější).
- Prompt struktura: Subject / Action / Camera / Environment; jemné pohyby (divoký pohyb rozbije kompozici).
