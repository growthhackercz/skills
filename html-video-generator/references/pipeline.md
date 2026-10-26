# Pipeline — produkční doktrína

Hlavní lekce (Sara Nambiar $500 experiment + naše iterace): **scéna není problém, produkční vrstva kolem je.** HyperFrames umí scénu; těžké je timing, kontinuita, audio sync, QA, surgical edity, assembly. Tahle doktrína je závazná.

## 5 fází

```
Intake  → načti brand+product DNA, typ, délka
Spec    → frame.md (motion spec z DNA) + styl + scénář + storyboard (timestamp sémantika)
Scene   → catalog blocky/vlastní kompozice, rebrand na frame.md, draft render
Sync    → HeyGen hudba + hravé SFX na beaty + ducking
Proof   → render QA (proof framy z MP4), kontinuita, surgical edity, assembly
```

## Layered build order (NIKDY vše najednou)

1. Draft scény (každá samostatně, schvaluj). 2. Master (assembly/audio bez captions). 3. Captions (pokud jsou). 4. Hudba + SFX. Malé změny zůstanou malé.

## Build backward from final frame (killer na iterace)

Před stavbou hero scény si **vyrobit concept image cílového framu** (FAL flux / GPT image) a stavět scénu, aby ho trefila. Konverzace „udělej to lepší" → „udělej to jako TOHLE". Drasticky míň iterací. Plánuj proof finálního framu.

**Reference-matching checklist** (porovnej scénu s referencí — proti FINÁLNÍMU framu, ne otevíracímu): počet objektů, relativní pozice, scale, váha písma, tloušťka linek, radius, teplota pozadí, měkkost stínů, umístění popisků, čitelnost při finálním holdu.

## Precizní prompting (chování, ne přání)

❌ „graf ať najíždí postupně" → ✅ „graf začne růst v 5s, 1. bod v 6s, 2. v 7s, finální v 10s; body se objeví až když k nim linka dojede."
❌ „sync audio líp" → ✅ „když řekne ‚Until now', začne titulek; než doříká větu, drž frame 2s, pak přechod."
Definuj **vztah mezi mluveným slovem a vizuálním stavem**, ne „synchronizuj".

## Sync na hlas přes whisper word-timestamps

Když má text/SFX padnout přesně na konkrétní slovo (a klient řekne „text skáče moc brzo"), nehádej — **změř hlas**:
1. Přepiš VO na slova s časy: `fal-ai/whisper` (`task:transcribe, language:cs, chunk_level:word`) → `chunks[].timestamp` dá přesný čas každého slova.
2. Posuň scénám `data-start` v `index.html` **a** vnitřní `tl.fromTo(…, offset)` tak, aby klíčový prvek naskočil na čas fráze; SFX dej `adelay` na ty samé časy.
3. ⚠️ Když VO beat má v mixu `atempo`/`adelay`, čas fráze v mixu = **`orig_ts / atempo + adelay`** (přepočítej, jinak ujede o ten posun).
4. B-roll klipy nech natěsno na jejich reálných délkách (track 0); text scény časuj **nezávisle** na B-roll předělech — předěl podkladu nemusí sednout s předělem textu.

## „Feels off" ladder (když to nepůsobí prémiově)

Zkontroluj v pořadí: **scale → spacing → barvy → motion timing → typografie.** Většina „není to prémiové" je z předimenzovaných prvků, moc barev, nebo nekontrolovaného pohybu.

## Iterace > generace

První verze není finální. Optimalizuj **cenu příští verze**, ne dokonalý první render. Scény jsou source-editable → malé změny malé. Draft kvalita při ladění, přesné FPS až na final. Staré rendery drž, dokud není náhrada ověřená.

## Ptej se jen na to, co mění implementaci

Neptej se na věci zjistitelné ze souborů. Ptej se jen, když odpověď mění, co postavíš (styl, koncept, breaking změna). Jinak NÁVRH + STOP (viz CLAUDE.md).
