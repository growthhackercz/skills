# Viral DNA Card™ — spec (v1)

Hloubkový rozbor **JEDNOHO vítězného donora** (reklama NEBO organický obsah) → DNA karta = **klon-šablona pro makery**. Výstup kroku **Dekóduj (hloubka)** a vstup do kroku **Neural Clone** metody Ad DNA Method™. Donor-agnostické — proto *Viral* DNA Card, ne „Ad" (rozebírá i content). Rodina: boardy = šířka („co vyhrává"), karta = hloubka („jak přesně tenhle vítěz funguje").

Build `scripts/dnacard_build.py` (deterministická kostra) → **MODEL doplní sémantiku** → renderer `scripts/dnacard.py` (design 1:1 z dema `documents/ads/scout/dna-deep-dive-demo/dna-card.html`). Golden běh: `documents/ads/scout/dna/tiktok-7556634102959557910/2026-07-13/` (kreatin, validováno naostro 2026-07-13).

## Tři úrovně (v1 = A + B; C nestavět)

| Úroveň | Co | Kdy | Náklad |
|---|---|---|---|
| **A · Kondenzát v boardu** | 3 mini-karty ve Viral Ad Boardu: nejlepší **Reklama** · **Organika** (short) · **Longform** — hook · úhel · proč vyhrál · jak se inspirovat (**max ~5 řádků/kus**) | default, předpočítané při buildu boardu (`dna_kondenzat` v rich-contractu) | skoro zadarmo (jede na už staženém textu) |
| **B · Standalone full karta** | plná Viral DNA Card jednoho donora (URL → karta) | na zavolání (`dna-fetch` / `dna-render`) | ~$0,10–0,18/karta (ladder níže) |
| **C · Batch full karty** | full karta pro každý top donor boardu | **v2 — ZATÍM NESTAVĚT** | 3× full |

Majitel malého byznysu je lean-back — hodnotu servíruj v boardu (A); full karta (B) je drill-down na vyžádání.

## Workflow (B — standalone)

```bash
# 1) VŽDY nejdřív dry-run (odhad + STOP — kredity jsou klientské peníze)
python3 {baseDir}/scripts/scout.py dna-fetch "<URL donora>" --tema "<téma>" --dry-run
# 2) ostrý fetch (meta + náhled + framy/přepis + komentáře; denní cache per donor)
python3 {baseDir}/scripts/scout.py dna-fetch "<URL donora>" --tema "<téma>"
# 3) MODEL doplní sémantiku do dna-card.json (viz „Co plní MODEL")
# 4) render
python3 {baseDir}/scripts/scout.py dna-render "<URL donora>"
```

Run-dir: `/documents/ads/scout/dna/<sit>-<id>/<datum>/` — `donor-raw.json` · `comments.json` · `thumb.jpg` · `video.mp4` + `frames/` (jen krátký formát) · `dna-card.json` (contract) · `viral-dna-card.html`. Flagy: `--no-comments` / `--no-transcript` / `--no-frames` / `--refresh`.

**Donor z boardu:** karta boardu už nese URL — předej ji `dna-fetch` (žádná zvláštní vazba). Ad Library deep-link (`facebook.com/ads/library/?id=…`) jede jako donor typu **reklama**.

## Analýza podle formátu (klíč = `donor.format`)

- **Dlouhé** (YouTube long / podcast / LinkedIn) → **jen přepis + 1 náhled** (DNA je v argumentu/úhlu). Titulky first (u YouTube ~zdarma v donor fetchi), žádné framy/vision.
- **Krátké** (reels / shorts / TikTok) → **framy + vision** (DNA je ve vizuálu: hook, first frame, tempo, text v obraze). Video se stáhne přes providera → ffmpeg (zdarma, lokálně) vytáhne 6 rovnoměrných framů → **vision dělá agent sám** (prohlédne thumb + framy), žádný extra model.
- **Temporal video-rozumění (externí model)** = z defaultu VEN; vzácný opt-in jen u krátkých, kde tempo rozhoduje a snímky to neutáhnou.

## Cost ladder (ověřeno naostro 2026-07-13, ceny BRONZE)

- Meta donora: ~$0,004–0,01 (1 kus). Video ke snímkům: +~$0,001 (add-on) + framy zdarma (ffmpeg).
- Přepis: YouTube titulky ~zdarma (součást donor fetche) · **TikTok = ASR titulky jsou často už u videa** (`videoMeta.subtitleLinks` → provider je stáhne zdarma z KV) · placená transkripce ~$0,04/započatá min jen když titulky nejsou.
- Komentáře: cap 60 × ~$0,001–0,00125 ≈ $0,06–0,075.
- **Celkem full karta: ~$0,10–0,18** (krátká i dlouhá zhruba stejně; cenu žene scrape komentářů, ne délka).

## Machine contract — `dna-card.json` (schéma)

```json
{
  "meta": {"skill":"ad-scout","vystup":"viral-dna-card","tema":"kreatin","trh":"cz","sken":"…","url":"…",
           "podtitulek":"volitelně — model může přepsat výchozí podnadpis karty (co karta dělá) na míru tématu"},
  "donor": {"sit":"tiktok","typ":"organika|reklama","format":"short|long|static",
            "nm":"český titulek","orig":"originál | null","kdo":"@…","url":"…",
            "kanal_url":"profil/kanál autora | null (renderer dovodí z url u TikTok/YT)","thumb":"/abs.jpg",
            "video":"/abs/video.mp4 | null (build doplní lokální kopii → play tlačítko + popup přehrávač)",
            "dur":"72","zhlednuti":N,"likes":N,"cmts":N,"shares":N,"engagement_pct":2.5,
            "dosah_eu":N,"dni":N,"varianty":N,"proc_donor":"proč je to dobrý donor (1–2 věty)"},
  "vizualni_dna": {"radky":[{"k":"Zastavení pozornosti","v":"… (smí <b>)"}],"vzorce":["…"],"frames":["/abs/frame-01.jpg"]},
  "textova_dna": {"radky":[{"k":"Titulek (hook)","v":"…"}],"kostra":"šok → příběh → …","kostra_zdroj":"přepis|odhad z textu"},
  "prepis": {"stav":"ok|chybi","text":"očištěný přepis (≤9000 zn.)","hook_3s":"mluvený hook česky","poznamka":"…"},
  "publikum": {"namitky":[{"q":"citace","e":"co signalizuje / jak použít"}],"touhy":[…],
               "fraze":["pilulka"],"triggery":["emoční tag"],"zdroj_pocet":N,"poznamka":"když vrstva chybí"},
  "klon": [{"typ":"V|H|U|F","nazev":"Vizuál","text":"… (smí <b>)"}],
  "_surovina": {"popis_raw":"…","komentare":[{"text":"…","likes":N}]}   // JEN pro model, nerenderuje se
}
```

## Co plní MODEL (sémantika — build nechává prázdné)

- **`donor.nm` česky + `orig`** (stejné pravidlo jako board: cizí titulek přelož, originál kurzívou pod ním) + **`proc_donor`** (trakce × relevance pro klienta, 1–2 věty). Renderer dává `nm` do **gradient nadpisu karty** (Viral DNA Card™ — „…") a `orig` kurzívou hned pod něj — `nm` je tedy hlavní titulek celé stránky, piš ho jako titulek.
- **`vizualni_dna`** — VISION: **prohlédni `thumb` + `frames/` očima** (Read) a popiš: zastavení pozornosti · titulek v obraze · důkazní/teasing prvky · důvěryhodnost · ověřená kostra. `vzorce` = 3–4 krátké chipy. Řádky `v` smí nést `<b>`.
- **`textova_dna`** — hook · úhel + fáze povědomí (česky!) · formát · nabídka/CTA; **`kostra`** z přepisu (když je), jinak odhad z titulku+popisu — a označ zdroj (`kostra_zdroj` plní build).
- **`prepis.hook_3s`** — mluvený hook z prvních ~3 s, přeložený do češtiny.
- **`publikum`** — destilát z `_surovina.komentare` (top podle lajků): ~5 námitek + ~5 tuh jako `{q, e}`, `fraze` (pilulky), `triggery` (tagy). **VŽDY ČESKY** (cizí komentáře přelož, mluvně). **Bez jmen** (GDPR — provider je strhal, nevracej je ani parafrází).
- **`klon`** — 4 řádky V/H/U/F (vizuál · hook · úhel · formát+nabídka) **přeložené na produkt/značku klienta** = hotové zadání pro makery. Přidej, co donor NEMÁ (např. CTA) jako klientovu výhodu.
- Vykání ke klientovi; žádné anglicismy na kartě (hook je povolený termín; „pattern interrupt" → zastavení pozornosti, „B-roll" → příběhové záběry apod.).
- **🛑 Slovo „donor" NIKDY v žádném textu, který klient uvidí** (radky, proc_donor, klon, poznámky). Je to jen interní klíč schématu — v obsahu piš **„předloha"** (příp. „tento kus"). Renderer používá „rozbor virální předlohy" / „Proč tato předloha".

## Kondenzát (A) — `dna_kondenzat` ve Viral Ad Boardu

Build boardu (`adboard_build`) předvyplní `{reklama, organika, longform}` — TOP-1 kandidát z každého světa (ref/nm/kdo/thumb/url/uhel/val). **Model doplní `hook` · `proc` · `inspirace`** (a volitelně `dna_url` na standalone kartu). Renderer (`adboard._dna_top3`) sekci **„Viral DNA — nejlepší kus z každého světa"** ukáže jen u vyplněných kbelíků; staré kontrakty bez klíče fungují beze změny. ⚠️ Kondenzát drž KRÁTKÝ (~5 řádků/kus) — jinak board zase přeteče.

## Ověřené actory (INTERNÍ — nikdy do výstupu; env přepíše #0 chainu)

Donor podle URL (`provider.DONOR_CHAINS`, ≥2 fallbacky/síť; ověřeno v Apify Store + naostro 2026-07-13):

| Síť | Chain: primární → zálohy | Pozn. |
|---|---|---|
| TikTok | `clockworks/tiktok-scraper` (postURLs; covers + video download + ASR titulky/transkripce v JEDNOM běhu) → `apidojo/tiktok-scraper` (startUrls, $0,0003) → `clockworks/free-tiktok-scraper` | env `AD_SCOUT_TT_DONOR_ACTOR`; ASR titulky chodí jako `videoMeta.subtitleLinks[].downloadLink` (VTT v KV, s ?token) — provider stahuje sám |
| YouTube | `streamers/youtube-scraper` (startUrls + `maxResults≥1`! + downloadSubtitles/plaintext) → `starvibe/youtube-video-transcript` (meta+transkript) → `beyondops/youtube-metadata-scraper-pro-v2` | env `AD_SCOUT_YT_DONOR_ACTOR` |
| Instagram | `apify/instagram-scraper` (directUrls) → `apify/instagram-api-scraper` | env `AD_SCOUT_IG_DONOR_ACTOR` |
| Facebook | `apify/facebook-posts-scraper` (startUrls) → `xtracto/facebook-post-detail` (posts) | env `AD_SCOUT_FB_DONOR_ACTOR` |
| Ad Library URL | `automation-lab/facebook-ads-library` (**`adsLibraryUrls`** — bere pasted deep-link) → `apify/facebook-ads-scraper` (startUrls, oficiální) → `azzouzana/meta-facebook-instagram-ads-library` (startUrl) | env `AD_SCOUT_ADLIB_DONOR_ACTOR` |

Záložní přepis (`provider.TRANSCRIPT_CHAINS`): YouTube `pintostudio/youtube-transcript-scraper` ($0,01) → `karamelo/youtube-transcripts` ($0,006). Komentáře donora = stávající `provider.content_comments` (chainy per síť, GDPR strhává autory na hranici providera).

## 🛑 Právo & GDPR (guardraily)

- **Stažení donora přes providera/proxy, NIKDY z klientské IP.** Video/obrázky **transient** — jen k rozboru, **nerehostují se** (copyright). Karta nese náhled + framy lokálně jako podklad analýzy + deep-link na originál; do klientských kampaní z nich nejde nic.
- **Komentáře bez jmen autorů** (GDPR) — strhává provider, model je nevrací ani parafrází.
- **Kredity:** `--dry-run` + STOP před ostrým během; denní cache per donor; full karty jen pro top donory / na vyžádání.
- **Karta = interní klon-šablona pro makery**, ne klientský rehost cizí reklamy.
- Sanitizace: reklamní registry + kanály jmenovat SMÍŠ; jména aktorů/„scraping" do výstupu nikdy (`output-sanitization.md`).

## Wiki (AI Data Center)

Destilát karty (`hook · kostra · úhel · formát · proč`) patří do vrstvy **Entity — Firma + štítek `konkurence`** (konvence competitor-tracker), znovupoužitelné vzorce do **Koncepty**, Raw Diet do **Zdroje**. Jen text-destilát, nikdy kreativa/frames. Chybí-li wiki → skip bez chyby (viz SKILL sekce Wiki).
