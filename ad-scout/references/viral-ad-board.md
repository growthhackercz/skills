# Viral Ad Board — spec

Výchozí výstup ad-scoutu. Osa = **klíčové slovo / téma**. Placené reklamy konkurence + organický virál pro **inspiraci kreativou** (jádro VIRAL DNA Cloning: donor → DNA → klon). Rodina: Viral Ad Board (téma) · Competitor Ad Board (značka) · Product Intelligence Board (produkt).

Renderer `scripts/adboard.py` (design 1:1 z golden dema, CSS+SVG v `_adboard_assets.py`). Build `scripts/adboard_build.py` (deterministická kostra). Golden pár: `assets/viral-ad-board-example.json` → `assets/viral-ad-board-example.html`.

## Sekce (STOHOVANÉ, ke klientovi VŠE česky — bez anglického žargonu pro SMB)
| Sekce | Vstup | Mechanika / co ukazuje |
|---|---|---|
| **Přehled** (4 staty) | odvozeno z dat | **Inzerentů na téma** (nasycení) · **Nejvirálnější** (peak zhlédnutí) · **Nejdéle běžící** (dní běhu = ověřené) · **Volné úhly** (příležitost). NE fetch cap — actionable signály. |
| **Mapa úhlů** | model | 🔴 plno / 🟡 sporné / 🟢 volno (s počty) — kde je prostor |
| **Proč se tím inspirovat** + **Knihovna hooků** | model | syntéza (fúze reklama × organika, 4–6 bodů) + top hooky (headline + vzorec + zdroj + proč) |
| **01 · Placené reklamy konkurence** | knihovna reklam | klonovatelná kreativa · **TOP 15** (4:5) · skóre = dosah EU × běh × varianty · **FB+IG → Meta** |
| **02 · Organický obsah** | organika | **Krátký obsah** (TikTok · IG Reels · YT Shorts · FB Reels → **hooky + formáty**, TOP 10, 4:5) + **Dlouhý obsah** (YouTube dlouhé · podcast · LinkedIn → **úhly + argumenty**, TOP 10, 16:9) · skóre = zhlédnutí × zapojení |
| **03 · Úhly ve vyhledávání** | výsledky vyhledávání | jaké komunikační **úhly** konkurence jede v searchu (**NE** share of voice, **NE** pozice) — třetí zdroj úhlů |
| **04 · Jazyk zákazníka** (Raw Diet) | komentáře pod TOP obsahem | námitky · touhy · doslovné fráze — **bez jmen** (GDPR) |

### Krátký vs dlouhý obsah — proč split
Nesou **jinou DNA**: short (reels/shorts) = **hooky + formáty** (craft prvních 3 s), long (YouTube dlouhé/podcast/LinkedIn) = **úhly + argumenty** (z přepisů se těží snadno). Klasifikace je deterministická (`content_format(net, dur)` v `adboard_build.py`, práh 180 s; `format` per kus). **LinkedIn/long-form je podmíněný typem tématu** — u B2C fyzického produktu skoro neexistuje; řídký long-form = signál díry (prostor pro long-form úhel), ne chyba.

## Discovery organiky — jak se obsah HLEDÁ (`provider.content_search`)
**Primární signál = KEYWORD SEARCH na všech sítích** (podle TÉMATU, ne hashtagu, ne watchlistu). Hashtag mine obsah, kde ho nikdo nedal; watchlist nemáme. Keyword search hledá v titulku/caption/textu → **obsah neuteče**. Hashtag/účty jen volitelný doplněk.

| Síť | Aktor (keyword search) | Do bucketu |
|---|---|---|
| TikTok | `clockworks/tiktok-scraper` (search) | Krátký |
| YouTube | `streamers/youtube-scraper` (`searchQueries[]`) | Dlouhý (+krátké shorts) |
| Instagram | `apify/instagram-scraper` (nativní `search`) → hashtag explore | Krátký |
| Facebook | `scraper_one/facebook-posts-search` (datum + engagement) | Krátký |
| **FB + IG naráz** | `seibs.co/meta-content-intel` (keyword + engagement + téma) | Krátký (a téma → i Jazyk zákazníka) |
| LinkedIn | `harvestapi/linkedin-post-search` (datum, reakce, sort) | **Dlouhý (B2B úhly)** — jen u B2B tématu |

`content_search(query, net, since=None, cap)` → normalizované virální kusy (`sit/nm/kdo/url/zhlednuti/likes/cmts/thumb`). `nm` je surový titulek, MODEL ho přeloží/shrne (max 3 řádky).

**Pozn.:** tabulka ukazuje **primární** actor; každá síť je od v0.2 **fallback chain** (primární + 2 zálohy) — přesné pořadí je zdroj pravdy v `provider.SEARCH_CHAINS` (když primární vrátí prázdno/chybu, kód zkusí další). IG jede přes **nativní `search`** v `apify/instagram-scraper` (ne ruční hashtag explore). Stejný vzor mají reklamy (`AD_CHAIN`) i komentáře (`COMMENT_CHAINS`).

**Časový limit → NENÍ tvrdý (rozhodnutí):** nejdřív „na co lidé reagují" = **engagement napřed**. Staré video s vysokým zapojením zůstává (lidé na něj reagují = validní virál). Řazení dotazu na relevance/top; **skóre + jen jemný bonus za čerstvost** (ne filtr, co vyhazuje). `since` = volitelná **široká pojistka** (např. 12–18 měsíců), ne 30/90 dní. **CZ→globál fallback:** fetch CZ napřed, když je CZ tenké, dopln globálem (badge GLOBÁL); build řadí CZ napřed (`geo != cz`).

**LOKÁLNÍ obsah má PŘEDNOST, angličtina jen když je ho málo (ZÁKLADNÍ PRAVIDLO).** Proč: mnoho termínů je cizojazyčně dominantních (např. „kreatin" = i německé hláskování; německý/globální trh je násobně větší → globální hledání vrací německy/anglicky, `_lang_ok` to zahodí → 0 českého). Řešení:
- **Krok 1 — lokální s geo-cílením:** český dotaz jede s **`market`** → TikTok `proxyCountryCode=CZ` (servíruje jako z Česka, ne globálně nejpopulárnější). YouTube i **Shorts** (`maxResultsShorts`). Lokální obsah je první.
- **Krok 2 — EN jen doplněk:** teprve když lokální < `per_platform`, agent zadá **anglický překlad**: `viral-fetch "<téma>" --en <english>` (např. `--en creatine`). EN dotaz jede **globálně** (`market=None`), sloučí se (dedup URL, cap 20/síť). Globální EN vítěze držíme (přeložený titulek + EN `orig`), ale **build řadí lokální (`geo != cz`) první** — angličtina nikdy nepředběhne české.

## Skóre (deterministicky, v `adboard_build.py`)
- **Reklama:** `55·log10(dosah)/6 + 35·min(dní,150)/150 + 10·min(varianty,8)/8`.
- **Organika:** `70·min(log10(zhlédnutí)/7,5;1) + 20·min(ER/8 %;1) + 10·min(kom./10k zhl. ÷ 20;1)` (ER = likes/views). **Dosah = hlavní faktor (70 %)** — miliony zhlédnutí musí táhnout, zapojení/diskuse jen dolaďují. ⚠️ Stropy schválně vysoko (dosah ~30 mil., ER 8 %) — první verze saturovala od ~316k zhlédnutí a všichni virální vítězové měli shodně 88.
- **Search:** share of voice = na kolika ze sledovaných klíč. slov se inzerent objeví.
- Tier badge: ≥75 hot · ≥55 warm · jinak cool.

## Co plní MODEL (sémantika — jako u produktu recenze→náměty)
- **Titulek karty (`nm`) — VŽDY česky + originál pod tím (`orig`). ZÁKLADNÍ PRAVIDLO, platí pro reklamy I organiku:**
  - **Cizojazyčný titulek** (anglicky…) → **přelož `nm` do češtiny** (přirozeně, ne doslovně) a **originál dej do `orig`** — renderer ho zobrazí kurzívou pod titulkem („opatrné", nic se neztratí). Platí i pro globální **anglické** vítěze (dlouhý obsah): český titulek + EN orig.
  - **Chybí titulek** (jen útržek „One chat.", handle, holý hashtag, useknutý text) → **shrň `nm` z textu příspěvku** (max 3 řádky); `orig` = původní útržek, když dává smysl, jinak `null`.
  - **Jasná česká copy** → `orig=null`.
  - Uvozovky NE na titulky (jen na citace zákazníků).
- **Reklamy — `nm` = REÁLNÁ kopie reklamy** (headline / nabídka konkurenta, vyčištěná od emoji a bold-unicode; cizí → přelož + `orig`), **NE generický titulek** typu „Značka — vybavení". Reálná copy JE ta konkurenční inteligence (např. „AKCE: kreatin + 300 g ZDARMA"). Dynamické **katalogy (`{{…}}`) se nezobrazují** (`provider._is_concrete_ad`). Když v CZ málo konkrétních reklam, kód doplní **ze zahraničí (SK/DE/AT/PL)** s badge `GLOBÁL` na aspoň TOP 10.
- **Organika — zdrojový jazyk = jen CZ / SK / EN.** Jiné jazyky (španělština, indonéština, němčina…) **na board NEPATŘÍ** — filtruje `_lang_ok`, hlídej i při kurátoraci. Pozor na falešné přátele (`creatinine` ≠ `creatine`).
- **Náhled reklamy = obrázek NEBO video (POVINNĚ).** Ad-library actor vrací media (`_ad_media_urls`: `imageUrls` / `videoPreviewUrls` / `videoUrls`) — karta ukáže obrázek, nebo poster videa s **play → přehrání v popupu** (`video_url`). Nikdy holé logo inzerenta.
- **Video díra = NEJVĚTŠÍ příležitost.** Když `pokryti.cz_video` je 0 / nízké (CZ konkurence **nejede video**), kód dotáhne **nejúspěšnější zahraniční VIDEOreklamy** (badge `GLOBÁL`, `video_inspo`, přehratelné). Model to v `mapa_uhlu.volno` (🟢) a `synteza` označí jako **hlavní příležitost** („konkurence nemá video = tvoje šance"; video má obří dopad) a zahraniční video slouží jako vzor ke klonování.
- **Úhel** (`uhel`): sémanticky posoudit copy → label úhlu. Taxonomie je **per téma** (pluggable `angle_rules`), ne natvrdo — startovní sada v `adboard_build.DEFAULT_ANGLE_RULES`, model ji přizpůsobí tématu.
- **Awareness** (`aw`): unaware / problem-aware / solution-aware / product-aware (Angle OS žebřík).
- **„Proč" 3 odrážky** (`why`): důkaz (běh/dosah/ER) + úhel + co si vzít.
- **Mapa úhlů** (`mapa_uhlu`): {plno:[{uhel,pocet}], sporne:[…], volno:[…]} — páruje „co zákazník cítí" × „co konkurence ignoruje". Sytí ze VŠECH tří zdrojů (placené + organika + search).
- **Syntéza** (`synteza`: [{icon,color,html}]) + **hooky** (`hooky`: [{cz,orig,vzorec,color,why,kdo,val}]).
- **Úhly ve vyhledávání — sekce 05** (`search_uhly`: [{**uhel, pocet, insight, priklady:[{head, kdo}]**}]) — z placených search výsledků vytáhni JAKÉ ÚHLY konkurence komunikuje (ne SoV). **MODEL to VYPLNÍ ručně a strukturovaně** — na auto-odvození ze `search` NESPOLÉHEJ: (a) používá **generickou taxonomii úhlů** (default rules jsou pro AI témata → u jiného tématu dá nesmysl typu „produktivita" u kreatinu — přizpůsob úhly TÉMATU); (b) `head` ze SERPu bývají **slepené sitelinky** („Kreatin pro svalový růstKreatin | Dr. Max…") → **rozděl na čisté jednotlivé headliny** a přiřaď inzerenta (`kdo`). Ke každému úhlu dej **`insight`** (jednu větu: co ten úhel slibuje / jak ho využít). Cíl: 3–5 úhlů, každý s pár čistými příklady — ať sekce reálně nese hodnotu, ne slepený blob.
- **Jazyk zákazníka / Raw Diet** (`jazyk_zakaznika`: {namitky:[…], touhy:[…], fraze:[…], **frustrace:[…], otazky:[…], triggery:[…]**, zdroj_pocet:{net:N}}) — z komentářů (`provider.content_comments`) destiluj: **námitky/obavy · touhy/přání · doslovné fráze** (jejich slova) · **frustrace ze současných řešení** (co zkoušeli a proč to nefungovalo → úhel „na rozdíl od X") · **otázky, které si kladou** (→ do reklamy odpověz) · **emoční triggery** (tagy emocí, co je pohánějí). **Bez jmen** (GDPR). Surové komenty do výstupu nejdou. Renderer vykreslí, co je vyplněné (chybějící vrstvy přeskočí). **Panely (namitky/touhy/frustrace/otazky) = položky `{q: doslovná citace, e: vysvětlení — co signalizuje / jak použít v copy}`, KONZISTENTNĚ 5 na panel** (ne někdy 3, jindy 5 — když je lajkovaných komentářů málo, sáhni i po méně lajkovaných / dalších zdrojích, ať má každý panel 5; renderer bere prvních 5, položka smí být i prostý string bez vysvětlení). Renderer zobrazí **citaci `q` v uvozovkách „…" + kurzívou** (patrné, že je to reálné tvrzení návštěvníka), vysvětlení `e` pod ní tlumeně. **Uvozovky patří JEN k těmto citacím zákazníků, NE na titulky karet** (ty jsou vytvořené titulky bez uvozovek). `fraze` = krátké pilulky (jen text), `triggery` = tagy emocí. **VŽDY ČESKY:** když jsou komentáře cizojazyčné (typicky anglicky u globálního obsahu), **PŘELOŽ do češtiny citaci `q` i vysvětlení `e`** — na boardu NIKDY nenech anglické (ani jiné cizojazyčné) citace zákazníků. Přirozený, mluvený překlad (zachovej tón), ne doslovný.
- **Podtitulek** (`meta.podtitulek`) — volitelně; když chybí, renderer vygeneruje default z tématu (vykání, účel boardu).
- **Kurátorování** top inzerentů (`curated[page] = {title,tr,aw,vzit,uhel}`) — přepíše deterministické fallbacky.
- **`format`** (short/long u virálních kusů) plní **deterministicky build** (`content_format`), model needitovat — leda opravit zjevný omyl.
- **Viral DNA kondenzát** (`dna_kondenzat` — úroveň A z `references/viral-dna-card.md`): build předvyplní TOP-1 kandidáta z každého světa (`reklama` · `organika` · `longform`; ref/nm/kdo/thumb/url/uhel/val). Model doplní **`hook` · `proc` · `inspirace`** (+ volitelně `dna_url` na standalone kartu). **Drž KRÁTKÉ (~5 řádků/kus)** — jinak board přeteče. Renderer sekci „Viral DNA — nejlepší kus z každého světa" ukáže jen u vyplněných kbelíků; nevyplněný kondenzát = žádná sekce (staré kontrakty fungují beze změny).

## Vlastní výherci (compounding vstup — volitelný)

`ad-analyst` posílá vítězné bloky zpět do scoutu (`evergreen-ads.json` → **`own-winners.json`**). Scout je bere jako volitelný vstup: `adboard_build.build(..., own_winners=[…])` → samostatný klíč kontraktu **`vlastni_vyherci`** (NE mezi konkurenty — nekazí ranking).
- Tvar položky (vstup): `{inzerent?, nm, orig?, uhel?, aw?, why?, url?, thumb?, score?, dosah_eu?, dni?}` — chybějící pole doplní model.
- **Vyjmuty ze sanitizace** — je to klientova vlastní kreativa (smí se jmenovat, badge „VÁŠ VÝHERCE").
- Jejich **úhly/hooky tečou do wiki vrstvy Koncepty** (znovupoužitelné vzorce pro příští kampaň).
- Renderer je zatím ignoruje (neznámý klíč = žádná chyba); vlastní strip s badgem = drobná budoucí polish.

## Pravidla vykreslení (drží renderer `adboard.py` v0.4)
- **Stohované ČÍSLOVANÉ sekce** (01 od mapy úhlů, každá = velké mono číslo + nadpis + podnadpis, styl jako Product board, bez oddělovače): **01 Mapa úhlů → 02 Proč se tím inspirovat (+ knihovna hooků) → 03 Placené reklamy → 04 Organický obsah (Krátká/Dlouhý) → 05 Úhly ve vyhledávání → 06 Jazyk zákazníka**. Nahoře nečíslovaný přehled (staty). Číslo se inkrementuje jen pro sekce, co reálně vzniknou (`secno()`).
- **Ke klientovi VŠE česky (SMB-friendly):** placené reklamy · krátká videa · dlouhý obsah · úvodní hook · úhel · fáze povědomí · jazyk zákazníka. Anglicismy (hook, awareness, share of voice, feed, engagement) jen interně, **ne na boardu**.
- **Progresivní zobrazení (proti přehlcení):** do HTML se **embednu ~20** na sekci (pro analýzu — mapa úhlů/hooky/volné úhly potřebují šířku), ale **hned se zobrazí jen `COLLAPSE_AT` = 10** + tlačítko **„Načíst dalších N ↓"** (JS `more()` odkryje zbytek, bez re-fetche). Náklad hlídá **denní cache** (fetch 1×/den/téma), ne tlačítko. Capy `AD_SHOW/SHORT_SHOW/LONG_SHOW=20`. Poměry: placené + krátký obsah **4:5** (5 sloupů), dlouhý obsah **16:9** (5 sloupů, `.gwide`).
- **Kolaps + síťový filtr se skládají přes CSS třídy** (`.grid.collapsed>.ocard:nth-child(n+11)` + `.ocard.nf-hide`), ne inline styl — filtr drží 10, load-more rozbalí.
- **Karty reklam:** video vs obrázek jasně odlišeno (štítek Video/Obrázek + play-overlay); **video s `video_url` se přehraje v POPUP/lightbox 9:16** (`openVid` → `#vpop`, ✕/Escape/klik mimo zavírá) — vertikální reklama se nemrší do 4:5 karty. Obrázková karta klik → otevře reklamu. Titulek karty bílý, fáze povědomí česky (`AW_CZ`: „hledá řešení" místo „solution-aware").
- **Sekce 05 (úhly ve vyhledávání):** per úhel = počet inzerentů + insight + příklady headline. **Sekce 06 (jazyk zákazníka):** doslovné fráze (pilulky) + emoční triggery (tagy) + 4 barevné panely — Námitky · Touhy · Frustrace ze současných řešení · Otázky, které si kladou.
- **Termín „hook/hooky"** (ne „háček") — pro klienta akcelerátoru srozumitelné.
- **FB + Instagram → jeden „Meta" badge** (ne dva). Ostatní kanály (TikTok/YouTube/LinkedIn) samostatně.
- **CZ priorita → globál fallback:** virál nejdřív CZ, doplnit globálem; globální kus = badge **GLOBÁL**.
- **Síťové filtry** (JS) u placené i OBOU organických sekcí (krátký/dlouhý) — data-driven podle přítomných sítí; skládají se s kolapsem. Reálné thumbnaily (stažené přes provider/proxy, `file://` fungují lokálně).
- **🛑 Lokální stahování náhledů VŽDY per kus podle jeho URL** (TikTok oEmbed `tiktok.com/oembed?url=…` → `thumbnail_url`; YouTube `i.ytimg.com/vi/<id>/hqdefault.jpg`), NIKDY podle indexu v poli — pole se mezi fetchem a buildem řadí/filtruje a index-pojmenované soubory se prohází mezi kusy (reálná chyba 2026-07-13: prohozené náhledy na boardu Kreatin).
- **`<title>` stránky = přesně hlavní nadpis** (`Viral Ad Board — „<téma>"`); stejné pravidlo platí pro všechny boardy rodiny (DNA karta = název kusu, Competitor = značka, Search = téma).
- **Vykání** ke klientovi.

## Sanitizace (rizikově vázaná — viz `output-sanitization.md`)
Zdroje Viral Ad Boardu = **reklamní knihovny + veřejná organika** = **nízké riziko** (veřejné registry). Řádek „zdroje" držíme obecný pro čistotu, ale Meta/Google jmenovat SMÍŠ. Srovnávače se tu netýkají.

## Machine contract (schéma)
```json
{
  "meta": {"skill":"ad-scout","vystup":"viral-ad-board","tema":"…","trh":"cz","sken":"…","podtitulek":"… | (volitelné, jinak auto)"},
  "pokryti": {"reklamy_relevantni":N,"inzerentu":N,"search":N,"viralni_kusu":N,"viral_cz":N,"viral_global":N,"short":N,"long":N,"median_behu":N,"vlastni_vyherci":N},
  "reklamy": [{"poradi":1,"inzerent":"…","site":["facebook","instagram"],"score":89,"dosah_eu":843842,"dni":132,"varianty":3,"url":"…",
               "nm":"český nadpis","orig":"originál | null","uhel":"…","aw":"solution-aware","why":["…","…","…"],"thumb":"/abs/path.jpg"}],
  "viralni": [{"poradi":1,"sit":"tiktok","format":"short|long","kdo":"@…","score":81,"zhlednuti":52100,"likes":…,"cmts":…,"url":"…","nm":"…","uhel":"…","why":["…"],"thumb":"…","dur":"…","geo":"cz|global"}],
  "search_uhly": [{"uhel":"…","head":"příklad headline konkurence","kdo":"značka"}],
  "jazyk_zakaznika": {"namitky":[{"q":"doslovná citace","e":"vysvětlení / jak použít"}],"touhy":[{"q":"…","e":"…"}],"frustrace":[{"q":"…","e":"…"}],"otazky":[{"q":"…","e":"…"}],"fraze":["krátká pilulka"],"triggery":["emoční tag"],"zdroj_pocet":{"youtube":N,"tiktok":N}},
  "vlastni_vyherci": [{"poradi":1,"vlastni":true,"inzerent":"Vy","nm":"…","uhel":"…","aw":"…","why":["…"],"url":"…","thumb":"…","score":88}],
  "dna_kondenzat": {"reklama":{"ref":1,"nm":"…","kdo":"…","thumb":"…","url":"…","uhel":"…","val":"295 dní běhu",
                    "hook":"… (model)","proc":"… (model)","inspirace":"… (model)","dna_url":null},
                    "organika":{"…":"…"},"longform":{"…":"…"}},
  "mapa_uhlu": {"plno":[{"uhel":"…","pocet":"9+"}],"sporne":[{"uhel":"…","pocet":"5"}],"volno":["…"]},
  "synteza": [{"icon":"i-eye","color":"hsl(…)","html":"…"}],
  "hooky": [{"cz":"…","orig":"… | null","vzorec":"…","color":"hsl(…)","why":"…","kdo":"…","val":"132 dní · 844 tis. EU"}]
  // `search` (syrové výsledky vyhledávání) zůstává vstupem buildu; renderer z něj odvodí `search_uhly`, když chybí.
}
```
Render: `python3 scripts/adboard.py <contract.json> <out.html>`.
