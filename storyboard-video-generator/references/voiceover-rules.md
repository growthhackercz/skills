# Voiceover Rules — Gemini 3.1 Flash TTS

Pravidla pro generování českého voiceoveru přes FAL `fal-ai/gemini-3.1-flash-tts` (default backend tohoto skillu).

## Workflow před TTS voláním (POVINNÉ otázky)

Skill se před spuštěním Kroku 2c **vždy zeptá na 2 věci:**

### 1. Pohlaví hlasu

> *„Mužský nebo ženský hlas?"*

Skill nabídne default voice preset podle volby:
- **Žena** → `Aoede` (warm, mid-30s, intimate)
- **Muž** → `Charon` (deep, authoritative)

User může chtít konkrétní alternativu — viz Voice presets níže.

### 2. Text scénáře — 5 variant

Pokud user nedodá vlastní text, skill nabídne **5 variant scénáře** podle různých storytelling úhlů:

| # | Úhel | Charakteristika |
|---|------|-----------------|
| 1 | **Minimalistický refrain** | Krátké rytmické věty, opakování klíčové fráze, prostor pro hudbu |
| 2 | **Smyslová poetika** | Metafory (světlo/voda/dotek), emocionálně vázaný popis benefitů |
| 3 | **Autorita značky** | Heritage / vědecké credibility (Swiss precision, klinické testy) |
| 4 | **Osobní rituál** | First-person (můj rituál, každé ráno), aspirační lifestyle pohled |
| 5 | **Slib výsledku** | Outcome-driven (stárnutí lze zpomalit, co získáš), promise + brand reveal |

User si vybere jednu nebo dá vlastní text. Pak teprve TTS volání.

**Příklad pro anti-aging:**

| # | Variant |
|---|---------|
| 1 | „Deset minut denně. Světlo, které vidí kůže. Bioptron MedÓl. Pleť, která mluví za sebe." |
| 2 | „Něco, co kůže pozná. Polarizované světlo, deset minut denně. Bioptron MedÓl. A pleť odpovídá." |
| 3 | „Švýcarská přesnost pro vaši pleť. Deset minut polarizovaného světla. Bioptron MedÓl. Věda, která zjemňuje." |
| 4 | „Můj rituál. Každé ráno. Deset minut s Bioptronem MedÓl. Pleť, kterou poznám v zrcadle." |
| 5 | „Stárnutí se nezastaví. Ale zpomalí. Deset minut světla denně. Bioptron MedÓl. Pleť, která zůstává sama sebou." |



## Proč Gemini, ne ElevenLabs

ElevenLabs Multilingual v2 byl předchozí default. Po testování byl swapnut za Gemini protože:

- **Méně robotický** — Gemini čte přirozeněji, ElevenLabs často zní jako commercial announcer
- **Inline emotion tags** — `[short pause]`, `[whispering]`, `[sigh]`, `[soft laugh]` Gemini interpretuje
- **`style_instructions` parameter** — natural-language popis tonality, tempa a dynamiky
- **70+ jazyků** včetně češtiny s nativně znějící prozódií
- **Voice presets** — Aoede (warm female), Callirrhoe, Sulafat, Charon, Kore, atd.
- **Cena** — srovnatelná s ElevenLabs

ElevenLabs zůstává jako legacy fallback v `generate-voiceover.py` (`backend: "elevenlabs"`).

## Brief.voiceover schema

```json
"voiceover": {
  "backend": "gemini",
  "language": "cs",
  "voice": "Aoede",
  "style_instructions": "Speak in Czech with...",
  "temperature": 0.75,
  "script": "Plný český text..."
}
```

| Pole | Default | Popis |
|------|---------|-------|
| `backend` | `"gemini"` | `"gemini"` nebo `"elevenlabs"` |
| `language` | `"cs"` | ISO kód jazyka — script automapuje na descriptive název („Czech (Czech Republic)") |
| `voice` | `"Aoede"` | Voice preset (viz níže) |
| `style_instructions` | warm default | Natural-language popis stylu (viz Best Practices) |
| `temperature` | `0.7` | 0.5 = konzistentnější/bezpečnější, 0.9 = expresivnější/proměnlivější |
| `script` | _povinné_ | Plný text k namluvení (s phonetic respelly pro brand names) |

## Voice presets (Gemini)

Empirický přehled — přesný popis se může změnit s update modelu. Vyzkoušej a porovnej.

| Voice | Vibe | Použití |
|-------|------|---------|
| **Aoede** | Warm, female, mid-30s, intimate | Premium wellness, beauty, home (default) |
| **Callirrhoe** | Female, calm, slightly older | Mature audience, autoritní voiceovery |
| **Sulafat** | Female, brighter, younger feel | Lifestyle, fashion, mladší cílovka |
| **Kore** | Female, neutral newsy | Informativní, educational |
| **Charon** | Male, deep, authoritative | Tech, B2B, finance |
| **Algieba** | Male, warmer, conversational | Testimonial, friendly brands |

Dál existují: `Achernar`, `Algenib`, `Achird`, `Alnilam`, `Autonoe`, `Despina`, `Enceladus`, `Erinome`, `Fenrir`, `Gacrux`, `Iapetus`, `Laomedeia`, `Leda`, `Orus`, `Pulcherrima`, `Puck`, `Rasalgethi`, `Sadachbia`, `Sadaltager`, `Schedar`, `Umbriel`, `Vindemiatrix`, `Zephyr`, `Zubenelgenubi`. Na FAL docs je full list, prochází se v Gemini docs.

## Best practices pro `style_instructions`

### 1. Continuous flowing delivery — NO pauses

```
✓ "Continuous, flowing delivery with NO pauses between sentences — let one sentence breathe naturally into the next."
```

Pauzy zní AI-roboticky. I když script má tečky, bez explicitního „NO pauses" Gemini vkládá nucenou pauzu po každé tečce. Pro 15s ad to ukrojí 2-3s, které pak chybí.

### 2. Graduation arc napříč větami

Místo flat tone definuj emocionální oblouk:

```
"GRADUATION ARC: start soft and slow on '[první věta]' (almost confided), gently lift on '[druhá věta]' (quiet conviction), settle on the brand name with calm authority (small breath of pride), close on '[poslední věta]' at MEDIUM pace — gentle landing, NOT dragged out or whispered."
```

Bez tohoto Gemini čte celý script monotónně.

### 3. Phonetic respell brand names přímo VE SCRIPTU

⚠️ **Nejdůležitější pravidlo.** TTS engine čte přesně co je napsáno. Cizí brand names čte podle naivních pravidel cílového jazyka, často špatně.

| Brand | Naivní (špatně) | Phonetic respell ve scriptu |
|-------|------------------|------------------------------|
| Aqueena | „A-kvíí-na" anglicky | **„Akvýna"** |
| Zepter | „Zepter" anglické Z | **„Ceptru"** (české C = ts) |
| MedAll | „med-ól" anglicky | **„MedÓl"** |
| Bioptron | OK v češtině, ale | **„Bi-op-tron"** zdůraznit B-I-O |

Postup:
1. Napiš script s phonetic respellem (script: „Akvýna od Ceptru…")
2. Doplň `style_instructions` poznámku co je co („'Akvýna' is the brand 'Aqueena', read as written")
3. Pokud Gemini přesto čte špatně, přepiš respell a regen

### 4. Tonalita / hlasová charakteristika

Doplň konkrétně:

```
"Female voice, mid-40s, warm, mature, composed. NOT a commercial announcer voice."
```

Klíčové je negativní omezení (`NOT announcer`) — bez toho Gemini sklouzává do commercial podání.

### 5. Inline emotion tags

Použij střídmě v scriptu:

```
"Pět minut denně. [short pause] Světlo, které vidí kůže."
```

Tagy:
- `[short pause]` — krátká pauza (~300ms), místo prosté tečky
- `[whispering]` — celý následující úsek šeptem
- `[sigh]` — povzdech
- `[soft laugh]` — jemný smích

⚠️ Kombinace „NO pauses" v `style_instructions` + `[short pause]` v scriptu je validní — explicitní `[short pause]` má prioritu, jen ostatní pauzy (po tečkách) se neaktivují.

## Příklad kompletní voiceover bloku

```json
"voiceover": {
  "backend": "gemini",
  "language": "cs",
  "voice": "Aoede",
  "style_instructions": "Speak in Czech with a warm, intimate, premium tone — like a confident woman in her 40s gently sharing a small daily ritual she trusts. Continuous, flowing delivery with NO pauses between sentences — let one sentence breathe naturally into the next. Natural Czech pronunciation, no robotic monotone. PRONUNCIATION RULES: 'Bioptron' is pronounced as Czech 'BI-OP-TRON' (3 syllables). 'MedÓl' is pronounced as Czech 'MED-ÓL' (long Ó as in 'móda'), NOT English 'med-all'. GRADUATION ARC across 5 beats: start with quiet matter-of-fact acceptance on 'Stárnutí se nezastaví' (soft, almost confided), gentle hopeful turn on 'Ale zpomalí' (slight lift), confident on 'Deset minut světla denně', settle on 'Bioptron MedÓl' with calm authority, close on 'Pleť, která zůstává sama sebou' at MEDIUM pace — calm satisfied landing. Female voice, mid-40s, warm, mature, composed. NOT a commercial announcer voice.",
  "temperature": 0.75,
  "script": "Stárnutí se nezastaví. Ale zpomalí. Deset minut světla denně. Bioptron MedÓl. Pleť, která zůstává sama sebou."
}
```

## Iterace

Když VO nesedí po prvním pokusu:

| Problém | Fix |
|---------|-----|
| Brand name čte anglicky | Přepiš v scriptu phonetic respellem („Aqueena" → „Akvýna") |
| Pauzy jsou moc dlouhé | Přidej „NO pauses between sentences" do style_instructions, smaž `[short pause]` tagy |
| Konec moc pomalý / dragged out | Přidej „closing line at MEDIUM pace, NOT dragged out or whispered" |
| Zní jako reklamní announcer | Přidej „NOT a commercial announcer voice", změň voice na Aoede/Algieba |
| Moc neutrální / flat | Doplň graduation arc s konkrétními emocemi po větách |
| Příliš expresivní / dramatický | Sniž `temperature` (0.5), přidej „calm, composed, restrained" |
| Špatný věk hlasu | Změň voice (mladší → Sulafat, starší → Callirrhoe) |
| Špatné pohlaví | Female → Male: Charon (deep), Algieba (warm) |

## Length & timing

Pro 15 s ad:
- **Optimální VO délka:** 10-13 s (necháváme 2-3 s instrumentální opening + outro)
- **Slov:** ~30-45 slov češtiny (rate: ~3 slova/s pro warm narration)
- **Vět:** 3-5 (delší věty = pomalejší, kratší = rytmičtější)

Pokud je script delší než 13 s, Gemini ho stejně namluví (nezkracuje), ale v ffmpeg post-mixu se může překrývat s outro music. Doporučuju zkrátit script a regen.

## Output

```
/documents/ads/video/[campaign-slug]/voiceover.mp3
```

Format: MP3, 24 kHz mono (Gemini default), ~120-160 kbps. ffmpeg post-mix v step 3b automaticky upsampluje na 44.1 kHz stereo a applikuje volume boost ×2.5 + sidechain ducking.

## Endpoint detaily

```python
endpoint = "fal-ai/gemini-3.1-flash-tts"
arguments = {
    "prompt": script,                          # plný text
    "voice": "Aoede",
    "style_instructions": style_text,
    "temperature": 0.75,
    "output_format": "mp3",
    "language_code": "Czech (Czech Republic)", # NE "cs" — Gemini chce descriptive jméno
}
```

⚠️ **`language_code` gotcha:** Gemini neakceptuje ISO kódy (`"cs"`, `"en"`). Vyžaduje descriptive form (`"Czech (Czech Republic)"`, `"English (US)"`). Skript `generate-voiceover.py` má LANG_MAP který tohle mapuje automaticky.

## Cena

Gemini 3.1 Flash TTS na FAL: ~$0.04 per 1M znaků input. Pro 50-znakový script = ~$0.000002. Prakticky zdarma vs Seedance video ($4.50 za 15 s) — iterace VO jsou levné.
