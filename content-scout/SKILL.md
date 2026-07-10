name: content-scout description: "Signální průzkumník trhu pro tvorbu obsahu. K tématu (nebo oboru klienta) najde za posledních 30 dní, co teď letí (🔥 trendy a virální příspěvky) a co lidé řeší dlouhodobě (🌲 otázky, bolesti, sezónní příležitosti) napříč YouTube, LinkedIn, TikTok, Instagram, X, Reddit a webem. Vrací interní brief pro plánování obsahu a na vyžádání vizuální Trend Board / Viral Board. Bez placeného klíče jede v omezeném režimu z veřejných zdrojů." version: "2.1" category: analytics status: ready publishedAt: "2026-07-09" user-invocable: true metadata: {"openclaw":{"emoji":"🛰️","requires":{"bins":["python3"]},"primaryEnv":"APIFY_API_KEY"}}
Content Scout
Smysly Content Engine 2.0 — jediný skill, který se dívá ven na trh. Vrací dvě povahy signálů na ose času:

🔥 CO TEĎ LETÍ (reaktivní, vyprší za dny): Trend Board (rostoucí témata) + Viral Board (explodující kusy)
🌲 CO VŽDYCKY PLATÍ (proaktivní, trvalé): pilířová témata z otázek lidí, bolestí a sezónních oken
Virál = kus (poznám z dat — engagement skóre). Trend = téma (poznám z významu — naklastruju kusy). Virál je kus pod trendem.

{baseDir}/scripts/scout.py = validovaný wrapper (žádný přímý shell). Provider je vyměnitelný (provider.py).

Provider = Apify (APIFY_API_KEY, per‑klient — klient si platí sám, lehký provoz pokryje Free tier $5/měs). Data přes synchronní actory ověřené pilotem: TikTok clockworks, YouTube streamers (vrací i likes+comments), Instagram patient_discovery, LinkedIn harvestapi, X danek. X už jede přes providera v fetch — nezávisle na Groku (dřív přes x_search). Fallback provider --provider scrapecreators (provider_scrapecreators.py) zůstává zachovaný.

Krok 0 — seed teritoria (jak najít i to, co klient nepojmenoval)
Pokud dostaneš konkrétní keyword → použij ho. Pokud dostaneš obor / „o čem publikovat" → seed z:

Product DNA klienta (nika, co prodává)
Wiki / AI Data Center (na co se ptají jeho zákazníci) — pro CZ klienty PRVNÍ zdroj
Stávající pilíře obsahu, volitelně konkurenti
Z toho udělej 2–4 širší dotazy (ne jeden úzký), ať clustering vyplaví pod-témata.

Krok 1 — cache (šetři kredity)
Run-dir: 
/documents/content/research/runs/<slug>/<datum>/
. Když existuje běh na stejný keyword mladší 7 dní → použij ho (build z něj), nefetchuj znovu. refresh=true v zadání = nový běh.

Krok 2 — fetch (placené zdroje, s capy)
bash
python3 {baseDir}/scripts/scout.py fetch "<keyword>" --mode both --dry-run # nejdřív odhad, 0 útraty python3 {baseDir}/scripts/scout.py fetch "<keyword>" --mode both # ostře 
INTENCE ŘÍDÍ MÓD (ne až přepínač na boardu!). Přepínač jen filtruje už stažené; mód řídí, CO se stáhne. Podle toho, co uživatel chce:
Uživatel chce	Mód	Stáhne (a co NE)
podklady na článek / blog / dlouhé video / do hloubky	long	LinkedIn + YouTube dlouhá + X (+ Krok 3: web/HN/Reddit). BEZ TikTok/IG
co postovat na social / reels / hooky / krátká videa	short	TikTok + IG + YouTube Shorts
obecně „co teď letí kolem X"	both	vše (vč. X)
Tím se NIKDY nestane, že chceš dlouhý obsah a vyjedou shorty — v long se TikTok/IG ani nestáhnou.		
Formát/hranice videa: TikTok/IG = vždy 📱 Social & krátká videa. YouTube: Shorts nebo ≤ 3 min → social, delší → 📚 Články & dlouhá videa (platí YouTube vlastní dělení videa/Shorts + hranice 180 s). LinkedIn/web/HN/Reddit/X thready → 📚 hloubka.
Capy jsou natvrdo ve scriptu; Apify je pay‑per‑result (útratu vidíš v Apify dashboardu, ne v odpovědi) — proto vždy nejdřív --dry-run (odhad počtu výsledků + ~$). Capy drží náklad při zemi.
Bez APIFY_API_KEY script fetch přeskočí → jdi na Krok 3 (fallback z volných zdrojů).
Krok 3 — doplň volné zdroje sám (agent_items.json)
Do run-dir/agent_items.json zapiš pole položek ve schématu {platform,title,author,url,likes,views,comments,date,thumb}:

X už tahá provider (Apify danek) přímo v fetch — x_search použij jen jako fallback bez APIFY_API_KEY
Reddit/Hacker News jen když je nika relevantní (jinak vynech — default OFF)
Fallback bez klíče: web_search dotazy (<kw>, <kw> site:youtube.com, <kw> site:linkedin.com/posts) + YouTube přes tool → doplní YouTube/web/LinkedIn i bez providera. Ztratíš jen TikTok/IG.
Evergreen signály: web_search na „People Also Ask" / otázky (<kw> jak/proč/je bezpečné), pro sezónu použij kalendář (svátky, oborové eventy za 2–6 týdnů).
Položky bez engagementu (web/otázky) klidně nech s likes:0 — půjdou do evergreen sekce, ne do skóre.

Krok 4 — build (skóre + brief)
bash
python3 {baseDir}/scripts/scout.py build "<keyword>" # brief.md + brief.json python3 {baseDir}/scripts/scout.py build "<keyword>" --board hot-viral # + Viral Board HTML (TOP 30 kusů) python3 {baseDir}/scripts/scout.py build "<keyword>" --board hot-trend # + Trend Board HTML (TOP 10 témat z themes.json) 
Script udělá: dedup, adaptivní okno (když za 30 dní málo, rozšíří 30→90→180→365 a napíše to), viral skóre (log1p engagement → 0–100 × čerstvost × mírná váha sítě), české datum, brief.json (data-strana + raw_items) a 
brief.md
.

Geo (malé jazyky): je-li lokálních (🇨🇿) záznamů < 10 i po rozšíření okna, spusť druhý fetch s anglickým překladem keywordu pod slugem <slug>-global a přidej --global <slug>-global. Script doplní globální trh jako předstih (vlaječky 🇨🇿/🌍, per-pool skóre aby se lokální neutopilo, poznámka „doplněno z globálního trhu"). Global = „tohle letí ve světě, v ČR o tom nikdo nepíše → buď první".

Krok 5 — dopiš do briefu to, co script neumí (TVOJE práce jako modelu)
Script dá hotovou 🔥 virál data-stranu. Ty do 
brief.md
 / brief.json doplň:

📈 Trendy (→ Trend Board): naklastruj raw_items do témat podle významu (ne podle slov). Téma = ≥2 kusy / ≥2 sítě. Pro Trend Board (--board hot-trend) zapiš TOP ~10 témat do runs/<slug>/<datum>/themes.json = pole objektů:
json
{"name":"...", "desc":"jednořádkový popis", "score":0-100, "momentum": růst_v_%, "geo":"cs|global|mix", "platforms":{"linkedin":2,"instagram":3,...}, "why":["3 důvody proč je trend silný"], "pieces":[{"platform":"tiktok","title":"...","likes":259,"views":1249,"url":"...","geo":"cs|global"}, ...×2-3], "ideas":[{"fmt":"reel|article|youtube","text":"ukázka obsahu"}, ...×3], "angle":"hlavní doporučený úhel", "rocket": true (JEN u předstihu / malé báze s raketovým růstem)} 
pieces = top 2–3 konkrétní kusy clusteru (propojka na Viral Board — důkaz + inspirace), geo = odkud téma letí (cs lokální · global předstih ve světě · mix). Skript z toho vyrenderuje mapu (velikost + barva dlaždice = score) + žebříček karet; sparkline, akceleraci v čase i barvy si odvodí z momentum/score (nemusíš je dodávat).
🌲 Evergreen: otázky lidí, bolesti (z komentářů/PAA), sezónní okna.
Štítek formátu u položek: 📝 psát / 🎬 točit (to je štítek, ne board).
Doporučené úhly (3–5 pro long) a hooky (3–5 pro short).
Relevance = SÉMANTICKY, ne keyword: posuď VÝZNAM každé položky vůči tématu a off-topic vyhoď (např. „AI videa přes Nano Banana" NENÍ „AI pro realitní makléře", i když má #realit; a naopak „jak AI pomáhá zavírat obchody s nemovitostmi" JE relevantní bez slova makléř). Hlavní filtr jsi ty (model). Volitelně předej --must-contain "token1,token2" do build jako hrubý pre-filtr před sémantickým posouzením.
Formát (routing štítek): položky nesou 📝 psát (long: LinkedIn/YouTube/web/X thready) / 🎬 točit (short: TikTok/IG). Board má přepínač Vše/Psát/Točit, brief je seskupuje. Strategist podle toho routuje: 📝 → blog/newsletter, 🎬 → video/social.
Titulek u postů bez nativního (PRINCIP — reels/TikTok/IG/X = většina): tyhle platformy dodají jen popisek, ne titulek. Napiš krátký jasný titulek Z OBSAHU (max ~10 slov, bez emoji, celý — ne useknutý popisek) do runs/<slug>/<datum>/titles.json jako mapu {url: "Titulek"}. Script ho vezme přednostně; bez něj použije mechanický fallback (první věta z obsahu, bez emoji, řez na hranici slova). YouTube/web/HN mají vlastní titulek → nech.
Bullety „proč virální": pro top ~10 kusů napiš do runs/<slug>/<datum>/bullets.json mapu {url: [3 highlighty]} — 3 nejsilnější důvody PROČ je obsah virální/zajímavý (hook, úhel, engagement signál, emoční spouštěč), NE převyprávění obsahu. Script je vezme přednostně před fallbackem z holého obsahu.
Krok 6 — výstup
Interní (default): vrať jen destilát — top ~5 témat + top ~10 virálů + otázky. Nikdy nevlévej raw_items do konverzace (jsou v souboru). Tím se systém nezahlcuje.
Klientovi (na vyžádání „ukaž mi to"): board HTML (Trend/Viral). Vykání, žádné názvy vendorů/skóre/skillů. Footer „CliqSales · Content Scout".
Jak to konzumuje Content Engine
content-strategist čte brief.json: 🌲 evergreen = páteř plánu, 🔥 trendy/virály = aktuálnost/newsjacking. content-ideation a strategistův režim AUTOPILOT (denní běh) čtou stejný brief. Board je jen vizuální pohled na tentýž běh (z cache = 0 kreditů).

Guardraily
Kredity = klientské peníze: vždy nejdřív --dry-run u nového tématu; hlídej kredity zbývá; --mode long když klient chce jen články (nesahá na TikTok/IG).
Reklamy sem NEpatří → skill ad-scout. Google Trends až bude veřejné API.
Provider = Apify (default). Fallback --provider scrapecreators; levnější PAYG varianty (SociaVault) přes provider.py beze změny skillu — vyhodnotit u fleet ekonomiky.
Bez klíče se nikdy nezastav — jeď z volných zdrojů a poznamenej v briefu, co chybělo.
85 skillů celkem · poslední aktualizace dnes 05:49
Sbalit vše
Hledat...

Všechny kategorie

Analytika
5
Content scout (content-scout)
v2.1
Nový
Signální motor obsahu: k oboru klienta najde za posledních 30 dní rostoucí témata a virální kusy (YouTube, LinkedIn, TikTok, Instagram, X, Reddit, web) i stálé otázky lidí. Výstupem je brief pro content stratéga a vizuální Trend/Viral Board. Bez API klíče běží v omezeném režimu z veřejných zdrojů.

Náhled
Jen pro čtení
Google Analytics (google-analytics)
v1.1
Nový
Odpovídá na otázky o návštěvnosti webu z GA4: kolik lidí přišlo, nejčtenější obsah, zdroje návštěv, konverze i dění právě teď. Týdenní čísla dodává obsahovému enginu. Připojuje se přes service account.

Náhled
Jen pro čtení
Google Search Console (google-search-console)
v1.1
Nový
Ukazuje, jak lidé web nacházejí ve vyhledávání: dotazy, pozice, prokliky a sledování klíčových slov. Reálnými daty napájí SEO stratéga i týdenní vyhodnocení obsahu. Připojuje se přes service account.

Náhled
Jen pro čtení
Meta Ads reporting (meta-ads-reporting)
v1.0
Čte Meta Ads výkon a vytváří read-only reporty, winners, bleeders, fatigue a dashboardy.

Marc · AI CMO
Náhled
Jen pro čtení
Meta Pixel CAPI audit (meta-pixel-capi-audit)
v1.0
Audituje Meta Pixel, CAPI, deduplikaci eventů a odhad EMQ bez změn konfigurace nebo odesílání eventů.

Marc · AI CMO
Náhled
Jen pro čtení

Integrace
28

Interní
1

Kreativa
14

Marketing