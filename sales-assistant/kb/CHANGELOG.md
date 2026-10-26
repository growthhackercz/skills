# CliqSales Closing System™ — changelog a verzování

**Jediný zdroj pravdy o verzi = soubor `VERSION`** (ne prose v INDEXu). Skripty ji čtou přes `kb_read.py --version`; mentor ji razítkuje do každého scorecardu (`meta.kb_verze`), takže u každého hodnocení navždy víš, podle jakých pravidel vzniklo.

## Sémantika bumpu (X.Y.Z)
- **MAJOR (X)** — změna **scoringu nebo taxonomie**: jiné váhy/kategorie, změna pravidla scoringu (např. pravidlo 5 urgence), přidání/odebrání typu námitky. **Mění srovnatelnost historických skóre** — skóre před a po MAJOR bumpu NEJSOU přímo porovnatelná (viz níže).
- **MINOR (Y)** — nová metoda / kapitola / příklad, aniž se mění jak se počítá skóre. Skóre zůstávají srovnatelná.
- **PATCH (Z)** — opravy, přesnější formulace, překlepy. Srovnatelnost beze změny.

## Jak updatovat pravidla (postup)
1. Uprav příslušnou kapitolu (`SCORING_ENGINE.md`, `belfort.md`, …).
2. Bumpni `VERSION` podle sémantiky výše.
3. Přidej řádek sem do changelogu (co a proč se změnilo).
4. Deploy: ZIP → programátor → nový image → fleet. KB je součástí každého konzumujícího skillu (`{baseDir}/kb/`); repo nemá automatickou synchronizaci těchto kopií, proto změnu KB proveď a otestuj záměrně ve všech konzumujících balících.
5. Od té chvíle nové scorecardy nesou novou `kb_verze`; staré zůstávají s původní.

## Srovnatelnost skóre přes MAJOR hranici
Po MAJOR bumpu (změna scoringu) upozorni v trendu, že se pravidla změnila: „od verze X.0 platí jiná pravidla, skóre před a po nejsou přímo srovnatelná." Mentor i analytik mají `kb_verze` u každého scorecardu, takže hranici poznají. MINOR/PATCH tohle neřeší.

## Historie

### 1.0 (revize 2026-07-30) — první fleet release

Verze zůstává `1.0`, protože knihovna nikdy nebyla na fleetu vydaná. Revize
2026-07-30 je oproti dřívějším pracovním verzím jiný obsah — proto tenhle
záznam popisuje **skutečně finální stav** a artefakt nese v názvu datum
i otisk obsahu (audit P2-02). Scoring ani taxonomie se nezměnily, takže
srovnatelnost skóre není dotčená.

Obsah metodiky:
- Univerzální metodika: Hormozi (CLOSER, Value Equation, belief breaking) + Belfort (Straight Line, Three Tens, 10 tonalit, looping/DISARM, prevence námitek, prahy) + Human-Centric (Trust Equity, Identity Shift — pro high-ticket).
- Scoring 0–100, 8 vážených kategorií, evidence-first, etický strop <60 při manipulaci.
- Pravidlo 5 (urgence): urgence a zavírání se odměňují u všech typů dealů; penalizuje se jen falešný/manipulativní tlak; u high-ticket urgence stojí na důvěře.
- Hybridní matice (SLS=OS, CLOSER<$5k, HCS>$5k). 100% generické (žádný klient-specifický obsah).

Co revize 2026-07-30 přidala (bez dopadu na scoring):
- `taxonomy.json` — jediný strojově čitelný zdroj kategorií, typů námitek
  a bodových pásem. Writer i analytik z něj čtou, `scorecard.schema.json` z něj
  bere enum a `SCORING_ENGINE.md` se proti němu kontroluje testem. Dřív byly
  stejné labely ručně opsané na čtyřech místech a mohly se nepozorovaně rozjet
  (audit P2-03).
- `scorecard.schema.json` vyžaduje hloubku, kterou `SKILL.md` slibuje —
  `verdict`, `parts[]` (≥ 2 části s názvem a popisem), `objections` (prázdné
  pole, když námitka nebyla), `closing_rozbor`, `signaly_cteni`,
  `coaching.plan` a cvičení. Prázdná kostra detailu už neprojde (audit P1-14).
- Knihovna se distribuuje **uvnitř každého konzumujícího skillu**
  (`{baseDir}/kb/`), ne jako sdílená `_lib` složka, kterou ZIP importér
  zahazoval (audit P1-16).
