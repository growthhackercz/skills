# Data a přihlášení — dashboardy i aplikace

Načti, když projekt **ukládá nebo zobrazuje data, která nemá vidět kdokoli**:
dashboard nad firemními čísly, klientský portál, evidence zakázek, rezervace,
interní přehled. Platí pro dashboardy i aplikace stejně — jedna datová cesta,
jeden způsob přihlášení, jedno pravidlo ochrany.

**Dělba práce:** `06-patterns.md` řeší **layout a komponenty** dashboardu (KPI
karty, grafy, tabulky, loading/empty/error stavy). Tenhle soubor řeší **odkud
data jsou, kdo je smí vidět a jak se to vynutí**. Neduplikuj je: mock data z
`lib/data.ts` (`05-stack.md`) jsou jen pro první náhled, ne pro odevzdání.

**Databáze i přihlášení jedou na Netlify.** Žádný další účet, žádný další
vendor, žádná další faktura pro klienta. Publikace beze změny přes
`netlify-publisher`.

## Krok 0 — rozhodni typ projektu

Než napíšeš řádek kódu, zařaď projekt. Špatné zařazení je nejdražší chyba
téhle reference: buď necháš firemní čísla veřejně, nebo naúčtuješ klientovi
přihlášení tam, kde stačila statická stránka.

| Typ | Poznáš podle | Data | Přihlášení |
|---|---|---|---|
| **A — statická stránka** | web, landing, prodejní stránka, kalkulačka, konfigurátor, kvíz bez ukládání | žádná (obsah v kódu) | **ne** |
| **B — dashboard nad daty** | čísla firmy, obrat, výkon kampaní; uživatel **jen čte** | čtení z DB, plní ji agent nebo cron | **ano, vždy** |
| **C — aplikace** | uživatel data **vytváří a mění**; víc lidí, role, oprávnění | čtení i zápis | **ano, vždy** |

**Typ A tenhle soubor nepotřebuje.** Zavři ho a jeď dál podle `06-patterns.md`.
Veřejná kalkulačka, která spočítá výsledek v prohlížeči a nikam ho neposílá,
nemá co chránit. Nepředražuj ji přihlášením.

**Typ B a C mají přihlášení VŽDY, i když si o něj klient neřekl.** Dashboard s
obratem, pohledávkami nebo výkonem kampaní na veřejné `*.netlify.app` adrese je
únik dat, ne feature. Neptej se, jestli ho chce — oznam, že tam bude:

> „Dashboard je za přihlášením — čísla vaší firmy nemají být na veřejné adrese.
> Založím účty pro lidi, které mi řeknete."

**Hraniční případ:** klient chce dashboard „jen pro sebe, ať to nezdržuje".
I tak přihlášení. Jeden účet je stejná práce jako pět.

## Krok 1 — vyber datovou cestu

Netlify má dvě. Vyber jednu, obě nikdy.

| | **Netlify Blobs** | **Netlify DB** (Postgres) |
|---|---|---|
| Balíček | `@netlify/blobs` | `@netlify/database` |
| Model | klíč → JSON dokument | tabulky, SQL |
| Zapnutí | **žádné**, funguje samo | `netlify database init` (jednou) |
| Adresa databáze | žádná | `getConnectionString()` z `@netlify/database` |
| Filtrování | jen `list({ prefix })` | plné SQL, `WHERE`, `JOIN`, `SUM` |
| Vezmi, když | účty, nastavení, do ~1 000 záznamů, žádné součty | dashboard s agregacemi, historie, vztahy mezi tabulkami |

**Pravidlo:** dashboard typu B skoro vždy **Netlify DB** (potřebuje součty a
období). Aplikace typu C s pár stovkami záznamů **Blobs**. Když váháš, ptej se:
*„Budu někdy potřebovat součet nebo řazení přes všechny záznamy?"* Ano → DB.

**Účty uživatelů drž vždy v Blobs**, i když data jedou v Postgresu. Ušetří to
migrační tabulku a přihlášení funguje dřív, než existuje schéma.

Po volbě nainstaluj **jen odpovídající řádek**. DB cesta potřebuje všechny tři
balíčky: Blobs pro účty a ochranné shardy, Database pro tagované SQL a `pg` pro
konektory/pool. Každý install má povinně stejný flag a hned svůj exec-bit fix:

```bash
# Datová cesta Blobs (také pro samotné přihlášení nebo lead formulář):
npm install --legacy-peer-deps --save-exact @netlify/blobs
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true

# NEBO datová cesta Netlify DB (účty stále žijí v Blobs):
npm install --legacy-peer-deps --save-exact @netlify/blobs @netlify/database pg
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true
```

**Limity a cena** (Netlify je od 4. 9. 2025 na kreditech):

- Free = **300 kreditů/měsíc s tvrdým stropem**. Po vyčerpání se web **pauzne**
  a návštěvník uvidí „Site not available". Na Free se kredity nedají dokoupit.
- Produkční deploy 15 kreditů, bandwidth 20/GB, compute 10/GB-hod.
- Personal $9 = 1 000 kreditů, Pro $20 = 3 000.
- Netlify DB: **5 GB na databázi**, Free 3 databáze, Personal 5, Pro 50.
  **Free a Personal databáze usínají po 5 minutách nečinnosti** — první
  požadavek po pauze trvá pár sekund. Klientovi to řekni dopředu, ať to
  nehlásí jako chybu.
- Blobs: max 5 GB na objekt, metadata 2 KB.

**Když klient jede na Free a aplikace má běžet denně, upozorni ho na strop
kreditů dřív, než mu web spadne.** Není to prodej, je to provozní fakt.

## Krok 2 — postav přihlášení

**Netlify Identity nepoužívej jako výchozí.** Existuje a je zdarma (deprecation
z února 2025 byla v únoru 2026 zrušena), ale **nedá se zapnout z příkazové
řádky** — `netlify identity` jako příkaz neexistuje a v API metodách taky nic
není. Jediná dokumentovaná cesta je proklikat to v Netlify UI, což znamená
poslat klienta klikat doprostřed workflow, který jinak běží celý sám.

Sáhni po Identity **jen** když klient výslovně chce samoobslužnou registraci
veřejných uživatelů, obnovu hesla e-mailem nebo přihlášení přes Google. Pak
mu dej instrukci proklikat Identity v Netlify UI a použij `@netlify/identity`
(ne starý `netlify-identity-widget`).

**Výchozí cesta: vlastní přihlášení ve funkci.** Heslo přes `scrypt`, session
přes podepsanou HttpOnly cookie, obojí ze `node:crypto` — žádná další
závislost. Účty zakládá agent, ne návštěvník.

### Dva klíče do prostředí

| Klíč | K čemu | Jak vyrobit |
|---|---|---|
| `SESSION_SECRET` | podpis session cookie | `openssl rand -hex 32` |
| `SETUP_TOKEN` | ochrana endpointu na zakládání účtů | `openssl rand -hex 16` |

Nahraj je přes publisher. `<publisherBaseDir>` je adresář `SKILL.md` načteného
skillu `netlify-publisher`; není-li dostupný, zastav se a požádej o jeho zapnutí:

```bash
# Hodnota se NIKDY nepředává argumentem (zůstala by v historii procesů).
# Publisher ji čte z proměnné Control Centra: nejdřív ji tam klient (nebo ty
# přes CC) založí, potom ji publisher propíše do prostředí webu.
python3 <publisherBaseDir>/scripts/netlify_publish.py env-set --site-id <id> --key SESSION_SECRET --from-variable CC_SESSION_SECRET --json
python3 <publisherBaseDir>/scripts/netlify_publish.py env-set --site-id <id> --key SETUP_TOKEN    --from-variable CC_SETUP_TOKEN    --json
```

**🛑 Hodnoty klíčů NIKDY nevypisuj** do chatu, do logu, do `netlify.toml`, do
souboru v projektu ani do zprávy klientovi. Do repozitáře patří jen
`.env.priklad` s popisem, čím se proměnná vyplní. Do `.gitignore` vždy `.env`.

⚠️ Proměnné zapsané v `netlify.toml` **nejsou dostupné funkcím**. Vždy přes
`env-set`, nikdy přes `netlify.toml`.

### Omezení pokusů o přihlášení (POVINNÉ)

Přihlašovací endpoint bez brzdy je pozvánka k hádání hesel. Počítadlo drž
v Blobs, databázi na to nepotřebuješ.

- Logické identity `email/<email>` i `ip/<ip>`, okno **15 minut**, limit **5 pokusů**
- Po překročení vracej **429** a nepouštěj dál ani se správným heslem
- Úspěšné přihlášení obě počítadla nuluje
- Odpověď nikdy neprozradí, jestli e-mail existuje: vždy „Nesprávný e-mail nebo heslo."
- **IP ber z `x-nf-client-connection-ip`**, ne z `x-forwarded-for` — ta jde podvrhnout

Kód patří do `_lib.mjs`, jinak si ho každý endpoint napíše po svém, nebo vůbec:

🛑 **Brzdu nepiš po paměti, zkopíruj ji.** Je v
`{baseDir}/references/auth.template.mjs` a je otestovaná
(`tests/test_auth.mjs`, mimo jiné 20 souběžnými pokusy).

Proč: `setJSON` při konfliktu **nevyhazuje výjimku**, vrací `{ modified: false }`.
Kdo ten výsledek ignoruje, má brzdu, která nebrzdí — pět souběžných pokusů
přečte stejné počítadlo a limit se překročí. Přesně na tom padla první verze.
Nový záznam navíc potřebuje `onlyIfNew`, existující `onlyIfMatch` na etag.

🛑 **Logická identita není název Blobu.** Šablona ji přes HMAC zařadí do
pevného počtu 64 stříd pro každý typ (`email` / `ip` / `heslo`). Jedna střída
drží nejvýš 128 aktivních digestů a při každém zápisu zahodí prošlé. Počet
Blobů je proto nanejvýš 192 a aktivní obsah má pevný strop; plná střída selže
zavřeně. Nedělej znovu `setJSON("email/" + email)`: validně vypadajících
e-mailů může útočník vyrábět bez omezení a takové klíče by zůstaly navždy.

V `prihlaseni.mjs` zavolej `brzda` pro e-mail i pro IP, po úspěšném přihlášení
obě `vynuluj`.

🛑 **Brzdu na e-mail volej až po ověření tvaru e-mailu.** Když se počítadlo
zakládá pro libovolný řetězec z těla požadavku, útočník ho nafoukne o miliony
klíčů a úložiště roste bez omezení. Nejdřív validace tvaru, teprve pak brzda.

🛑 **Brzda patří i na `nastavit-heslo.mjs`.** Je to neautentizovaný endpoint,
který sahá do Blobs a při úspěchu spouští drahý scrypt; bez brzdy ho lze
spamovat a na free tarifu s tvrdým stropem kreditů tím jde **pozastavit
klientovi celý web**. Brzdi na IP. Reset už nikdy nesmí volat `list()` — token
se hledá přímo podle HMAC digestu.

### Sdílená vrstva — `netlify/functions/_lib.mjs`

🛑 **Zkopíruj `{baseDir}/references/auth.template.mjs` jako
`netlify/functions/_lib.mjs`.** Nepiš tuhle vrstvu znovu a needituj ji „jen
maličko" — je otestovaná a každá úprava musí nejdřív projít
`tests/test_auth.mjs`.

Co šablona umí:

| Funkce | K čemu |
|---|---|
| `hashHesla` / `overHeslo` | scrypt + `timingSafeEqual` (nikdy `===`) |
| `vytvorToken` / `overToken` | podepsané sezení s platností a **verzí** |
| `prihlasenyUzivatel` | ověří podpis I to, že sezení nebylo odvoláno |
| `odvolejSezeni` | zvýší verzi → **všechna dosud vydaná sezení padnou** |
| `brzda` / `vynuluj` | bounded shardy počítadel s podmíněným zápisem a úklidem |
| `spotrebujResetToken` | přímý digest lookup + atomické single-use přivlastnění |
| `ctiTelo` / `jeEmail` / `jeHeslo` | poškozené a přerostlé vstupy bez pádu funkce |
| `ROLE` | výčet `majitel` · `spravce` · `uzivatel` |

🛑 **Na chráněných trasách používej VÝHRADNĚ `prihlasenyUzivatel()`.**
Lehký `prihlaseny()` ověří jen podpis — obchází odvolání sezení, zakázaný účet
i změněnou roli. Je použitelný leda tam, kde nejde o data (např. přesměrování
v UI). Každý datový endpoint (Blobs i DB) musí sáhnout po přísném helperu.

**`odvolejSezeni` volej vždy po:** změně hesla, zákazu nebo smazání účtu
a změně role. Bez toho zůstane útočník přihlášený i po tom, co mu klient
heslo změní — sezení je podepsané, ne uložené.

Cookie **musí** mít všechny čtyři: `HttpOnly` (JavaScript se k ní nedostane),
`Secure`, `SameSite=Strict`, `Max-Age`. Vynechání kterékoli je díra.

### Přihlašovací endpoint — `netlify/functions/prihlaseni.mjs`

```js
import { uzivateleStore, overHeslo, vytvorToken, cookieHlavicka,
         prihlasenyUzivatel, brzda, vynuluj, json, ctiTelo,
         normalizujEmail, jeHeslo } from "./_lib.mjs";

export default async function (req) {
  if (req.method === "GET") {            // kdo jsem
    const u = await prihlasenyUzivatel(req);
    return u ? json({ prihlasen: true, email: u.email, role: u.role }) : json({ prihlasen: false }, 401);
  }
  if (req.method === "DELETE")           // odhlášení
    return json({ ok: true }, 200, { "set-cookie": cookieHlavicka(null) });
  if (req.method !== "POST") return json({ chyba: "jen GET/POST/DELETE" }, 405);

  const telo = await ctiTelo(req);
  if (!telo) return json({ chyba: "neplatné tělo požadavku" }, 400);
  const { email: zadanyEmail, heslo } = telo;
  const email = normalizujEmail(zadanyEmail);
  // Tvar e-mailu se ověřuje PŘED brzdou: jinak by šlo zakládat počítadla pro
  // libovolný řetězec a úložiště by rostlo bez omezení.
  // Typ i délku hesla ověř PŘED scryptem a lookupem. Objekt, pole ani dlouhý
  // řetězec nesmí shodit endpoint na 500 a prozradit tak existenci účtu.
  if (!email || !jeHeslo(heslo))
    return json({ chyba: "nesprávný e-mail nebo heslo" }, 401);
  // Brzda před ověřením hesla. IP z hlavičky Netlify, ne z x-forwarded-for
  // (ta jde podvrhnout).
  const ip = req.headers.get("x-nf-client-connection-ip") || "?";
  for (const klic of [`email/${email}`, `ip/${ip}`]) {
    const { blok, za } = await brzda(klic);
    if (blok) return json({ chyba: `Příliš mnoho pokusů. Zkuste to za ${Math.ceil(za / 60)} minut.` }, 429);
  }
  const zaznam = await uzivateleStore().get(email || "", { type: "json" });
  // Stejná hláška pro neexistující účet i špatné heslo — neprozrazuj, kdo existuje.
  // Účet bez nastaveného hesla (jen s odkazem) se nepřihlásí.
  // Zakázaný účet se nepřihlásí — a nesmí se to poznat od špatného hesla.
  // Ověření volej VŽDY: helper pro chybějící/poškozený hash udělá dummy scrypt,
  // aby účet nešel poznat ani podle kratší odezvy.
  const hesloPlati = overHeslo(heslo, zaznam?.hash);
  if (!zaznam || zaznam.zakazan || !hesloPlati)
    return json({ chyba: "nesprávný e-mail nebo heslo" }, 401);
  await Promise.all([vynuluj(`email/${email}`), vynuluj(`ip/${ip}`)]);

  return json({ ok: true, email: zaznam.email, role: zaznam.role }, 200,
    // 🛑 Podepiš AKTUÁLNÍ tokenVerze. S implicitní nulou by po první revokaci
    //    nešlo se přihlásit vůbec — přísný helper by nový token odmítl.
    { "set-cookie": cookieHlavicka(vytvorToken(zaznam.email, zaznam.tokenVerze ?? 0)) });
}

export const config = { path: "/api/prihlaseni" };
```

### Zakládání účtů — `netlify/functions/setup.mjs`

**Veřejná registrace se negeneruje.** Účty zakládá agent po deployi voláním
tohoto endpointu se `SETUP_TOKEN` v hlavičce. Klient dodá seznam e-mailů a rolí.

```js
import { randomBytes } from "node:crypto";
import { uzivateleStore, resetTokenyStore, digestResetTokenu,
         json, ctiTelo, normalizujEmail, ROLE } from "./_lib.mjs";

const PLATNOST_H = 24;
// ROLE se importuje ze šablony (majitel · spravce · uzivatel).

export default async function (req) {
  if (req.method !== "POST") return json({ chyba: "jen POST" }, 405);
  if (req.headers.get("x-setup-token") !== process.env.SETUP_TOKEN)
    return json({ chyba: "neplatný setup token" }, 403);

  // Heslo se sem ZÁMĚRNĚ neposílá — skončilo by v transkriptu i v logu.
  const telo = await ctiTelo(req);
  if (!telo) return json({ chyba: "neplatné tělo požadavku" }, 400);
  const { email: zadanyEmail, role = "uzivatel", obnovit = false } = telo;
  const email = normalizujEmail(zadanyEmail);
  if (!email) return json({ chyba: "email je povinný a musí být platný" }, 400);
  // Role je výčet, ne libovolný řetězec z těla požadavku.
  if (!ROLE.includes(role)) return json({ chyba: `role musí být jedna z: ${ROLE.join(", ")}` }, 400);

  const store = uzivateleStore();
  const nacteno = await store.getWithMetadata(email, { type: "json" });
  const stavajici = nacteno?.data ?? null;
  // Zapomenuté heslo nesmí být slepá ulička: se `obnovit: true` se vydá nový
  // jednorázový odkaz. Chráněné je to pořád stejným SETUP_TOKENEM.
  if (stavajici && !obnovit)
    return json({ chyba: "uživatel už existuje (nový odkaz: obnovit: true)" }, 409);

  const token = randomBytes(24).toString("base64url");
  const digest = digestResetTokenu(token);
  const resetVerze = (stavajici?.resetVerze ?? 0) + 1;
  const tokenStore = resetTokenyStore();
  const tokenKlic = `v1/${digest}`;
  const tokenVysledek = await tokenStore.setJSON(tokenKlic, {
    email, resetVerze, tokenDo: Math.floor(Date.now() / 1000) + PLATNOST_H * 3600,
    pouzit: null,
  }, { onlyIfNew: true });
  if (!tokenVysledek?.modified) return json({ chyba: "odkaz se nepodařilo vytvořit" }, 503);

  const novy = {
    ...(stavajici || {}),
    email, role: stavajici?.role ?? role,
    hash: stavajici?.hash ?? null,
    resetKlic: digest, resetVerze,
    zalozen: stavajici?.zalozen ?? new Date().toISOString(),
  };
  const podminka = stavajici ? { onlyIfMatch: nacteno.etag } : { onlyIfNew: true };
  const ucetVysledek = await store.setJSON(email, novy, podminka);
  if (!ucetVysledek?.modified) {
    await tokenStore.delete(tokenKlic).catch(() => {});
    return json({ chyba: "účet se mezitím změnil; opakujte požadavek" }, 409);
  }
  if (stavajici?.resetKlic && stavajici.resetKlic !== digest)
    await tokenStore.delete(`v1/${stavajici.resetKlic}`).catch(() => {});

  // Odkaz je bearer tajemství. Zachyť ho jen pro přímé předání mimo
  // persistovaný chat, task, ticket a log; bezpečnější je transakční e-mail.
  return json({ ok: true, email, role: novy.role, odkaz: `/nastavit-heslo?token=${token}` });
}

export const config = { path: "/api/setup" };
```

`normalizujEmail()` je součást identity, ne jen kosmetika: setup, login,
session token i administrační helpery používají vždy `trim().toLowerCase()`.
`Owner@Example.com` a `owner@example.com` jsou proto tentýž účet a v Blobs
nemohou vzniknout dva účty sdílející jeden kanonický tenant namespace.

### Nastavení hesla — `netlify/functions/nastavit-heslo.mjs`

```js
import { uzivateleStore, resetTokenyStore, spotrebujResetToken,
         hashHesla, json, ctiTelo, brzda, jeHeslo } from "./_lib.mjs";

export default async function (req) {
  if (req.method !== "POST") return json({ chyba: "jen POST" }, 405);
  // Neautentizovaný endpoint sahá do Blobs a při úspěchu spouští scrypt → bez
  // brzdy jde spamem vyčerpat kredity tarifu a pozastavit klientovi celý web.
  const ip = req.headers.get("x-nf-client-connection-ip") || "?";
  const { blok, za } = await brzda(`heslo/${ip}`);
  if (blok) return json({ chyba: `Příliš mnoho pokusů. Zkuste to za ${Math.ceil(za / 60)} minut.` }, 429);

  const telo = await ctiTelo(req);
  if (!telo) return json({ chyba: "neplatné tělo požadavku" }, 400);
  const { token, heslo } = telo;
  if (typeof token !== "string" || !jeHeslo(heslo))
    return json({ chyba: "token a heslo (10–200 znaků) jsou povinné" }, 400);

  // Přímý HMAC-digest lookup; žádné list() ani procházení všech účtů.
  // CAS uvnitř helperu dovolí použít token právě jednomu souběžnému requestu.
  const pouziti = await spotrebujResetToken(token);
  if (pouziti?.stav === "vyprsel") {
    await resetTokenyStore().delete(pouziti.klic).catch(() => {});
    return json({ chyba: "odkaz vypršel" }, 410);
  }
  if (pouziti?.stav !== "ok") return json({ chyba: "neplatný odkaz" }, 400);

  const store = uzivateleStore();
  const nacteno = await store.getWithMetadata(pouziti.email, { type: "json" });
  const u = nacteno?.data;
  const digest = pouziti.klic.slice(3);
  if (!u || u.resetVerze !== pouziti.resetVerze || u.resetKlic !== digest)
    return json({ chyba: "neplatný odkaz" }, 400);

  // Změna účtu je také pod CAS: role/zákaz změněný souběžně se nepřepíše.
  const vysledek = await store.setJSON(pouziti.email, {
    ...u, hash: hashHesla(heslo), resetKlic: null,
    tokenVerze: (u.tokenVerze ?? 0) + 1,
  }, { onlyIfMatch: nacteno.etag });
  if (!vysledek?.modified) {
    return json({ chyba: "účet se mezitím změnil; vyžádejte nový odkaz" }, 409);
  }
  await resetTokenyStore().delete(pouziti.klic).catch(() => {});
  return json({ ok: true });
}

export const config = { path: "/api/nastavit-heslo" };
```

Účet s `hash: null` se nepřihlásí — `prihlaseni.mjs` na to musí pamatovat.

🛑 **Hesla nikdy neposílej chatem.** Zůstala by v transkriptu i v exportu.
`setup.mjs` proto heslo **nepřijímá**: vygeneruje `randomBytes(24)`, uloží jen
HMAC digest v samostatném indexu a vrátí bearer odkaz
`/nastavit-heslo?token=…`. Druhý endpoint provede přímý digest lookup a přes
CAS token atomicky spotřebuje, takže dva souběžné requesty nemohou uspět.
Bearer odkaz **nikdy nevkládej do persistovaného chatu, tasku, ticketu ani
logu**; předej ho přímo bezpečným dočasným kanálem, ideálně transakčním
e-mailem. Heslo si nastaví uživatel. Účet bez nastaveného hesla se nepřihlásí.

## Krok 2b — napojení na cizí systémy (dashboardy typu B)

Dashboard nad firemními čísly potřebuje data z Fakturoidu, banky, reklamy nebo
analytiky. **Nepiš to od nuly.** Existuje knihovna hotových konektorů:

```
cs-skills/_lib/connectors/
├── _template/               ← kostra pro nový konektor (má vlastní README)
├── fapi/                    ← tržby, faktury, objednávky, zákazníci
├── fio/                     ← zůstatek, pohyby, cashflow
├── ga4/                     ← návštěvnost
└── google-search-console/   ← dotazy a pozice ve vyhledávání
```

Každý konektor je samostatný TypeScript modul se šesti soubory: `auth.ts`
(načte klíče z prostředí a sestaví hlavičky), `operations.ts` (operace nad API
a hotové recepty), `schema.sql` (tabulky), `refresh.ts` (stažení a zápis do DB),
`docs.md` a `README.md`. **Zkopíruj modul do projektu a používej jeho operace**,
místo psaní vlastních volání.

⚠️ **Fakturoid konektor zatím NEEXISTUJE** (v knihovně je veden jako TODO),
přestože ho materiály i `sync-creds` uvádějí. Když ho klient chce, řekni to
rovnou a nabídni FAPI nebo postavení konektoru podle `_template/`.

### Odkud se berou klíče

Klient je zadá **jednou** v Control Centru (Integrace). Do prostředí webu je
přenášíš do prostředí webu **po jedné**, příkazem
`env-set --key <NAZEV> --from-variable <CC_PROMENNA>`.

🛑 **`sync-creds` nepoužívej.** V aktuálním publisheru **záměrně nic nedělá**
(fail-closed no-op), takže by ses spolehl na hromadný přenos, který neproběhne,
a dashboard by zůstal prázdný bez jediné chybové hlášky.

🛑 **Klíč nikdy nepiš do kódu, do `netlify.toml` ani do stránky.** Sahá po něm
výhradně serverová část. Kdyby skončil v kódu stránky, přečte si ho každý
návštěvník.

### Jak se data dostanou do dashboardu

Nikdy ne přímo z prohlížeče do cizího systému. Vždy tahle cesta:

1. `refresh.ts` konektoru stáhne data a zapíše je do Netlify DB.
2. Spouští ho plánovaná funkce (cron v `netlify.toml`) — **tenhle plán generuješ
   ty**, jinak se data po prvním stažení už nikdy neobnoví.
3. Po nasazení proběhne první stažení (`trigger-refresh` v publisheru), aby
   dashboard nesvítil prázdný.
4. Dashboard čte **z Netlify DB**, ne z cizího systému. Proto se otevře hned
   a funguje i ve chvíli, kdy s agentem nikdo nemluví.

**Interval volí obor, ne zvyk.** Tržby a cashflow denně, reklama denně,
návštěvnost denně. Častěji jen s důvodem: každý běh zatěžuje cizí systém a
některé mají tvrdé limity (Fio propustí jeden dotaz za 30 sekund).

### Konektory jsou read-only

Z cizího systému se **jen čte**. Žádný zápis, žádné mazání, ani když si o to
klient řekne. Dashboard je pohled na data, ne jejich správa.

### Když konektor pro systém není

Postav ho podle `_lib/connectors/_template/` (má krok-za-krokem README).
Potřebuješ k tomu od klienta **odkaz na dokumentaci** jeho systému a přístup
v Integracích. Bez dokumentace si názvy a adresy vymyslíš a konektor nepojede —
proto ji vyžaduj, než začneš.

## Krok 3 — chraň data, ne obrazovku

**Skrytí v UI není ochrana.** Když frontend jen nezobrazí tlačítko, data pořád
leží na `/api/…` pro kohokoli s prohlížečem. Ochrana patří **do funkce**.

Tři pravidla, všechna povinná:

1. **Každý datový endpoint začíná kontrolou session.** Bez ní 401, hned na
   prvním řádku, před jakýmkoli dotazem do dat.
2. **Vlastníka bereš ze session, nikdy z požadavku.** `vlastnik` v těle
   requestu nebo v URL parametru je vždy útok, ne data.
3. **Filtr je na serveru.** Nikdy nepošli všechno a nefiltruj v prohlížeči.

### Blobs

```js
import { getStore } from "@netlify/blobs";
import { prihlasenyUzivatel, tenantKlic, json } from "./_lib.mjs";
import { randomUUID } from "node:crypto";

export default async function (req) {
  const u = await prihlasenyUzivatel(req);
  if (!u) return json({ chyba: "nepřihlášen" }, 401);   // pravidlo 1
  const tenant = tenantKlic(u.email);
  if (!tenant) return json({ chyba: "neplatná identita účtu" }, 401);

  const store = getStore({ name: "zaznamy", consistency: "strong" });

  if (req.method === "POST") {
    const { nazev, castka } = await req.json();
    const z = { id: randomUUID(), vlastnik: u.email, nazev, castka: Number(castka) || 0 };
    //                            ^^^^^^^^^^^^^^^^ ze session — pravidlo 2
    await store.setJSON(`v1/${tenant}/${z.id}`, z);      // opaque tenant prefix
    return json({ ok: true, zaznam: z }, 201);
  }

  const { blobs } = await store.list({ prefix: `v1/${tenant}/` }); // pravidlo 3
  const data = await Promise.all(blobs.map((b) => store.get(b.key, { type: "json" })));
  return json({ pocet: data.length, zaznamy: data });
}

export const config = { path: "/api/zaznamy" };
```

Klíč vždy `v1/${tenantKlic(email)}/${id}`. Raw e-mail do klíče nepatří:
obsahuje znaky řízení prefixu a dovolil by kolizi typu `a@b.cz` vs.
`a@b.cz/evil`. Namespace je stabilní SHA-256 kanonického e-mailu (trim +
lowercase), nikoli HMAC se `SESSION_SECRET`; rotace přihlašovacího tajemství
proto data neodpojí. Hash zde neskrývá identitu před offline hádáním — jeho
účelem je bezpečný přesný prefix. Bez něj může `list()` vrátit data jiného účtu.

### Netlify DB

```js
import { getDatabase } from "@netlify/database";
import { prihlasenyUzivatel, json } from "./_lib.mjs";

export default async function (req) {
  const u = await prihlasenyUzivatel(req);
  if (!u) return json({ chyba: "nepřihlášen" }, 401);

  // 🛑 getDatabase() vrací OBJEKT { driver, sql, pool, connectionString },
  //    ne tagovanou šablonu. `const sql = getDatabase()` spadne na
  //    "TypeError: sql is not a function". Vždy destrukturuj.
  const { sql } = getDatabase();

  if (req.method === "POST") {
    const { nazev, castka } = await req.json();
    const [radek] = await sql`
      INSERT INTO zakazky (vlastnik, nazev, castka)
      VALUES (${u.email}, ${nazev}, ${Number(castka) || 0})
      RETURNING *`;
    return json({ ok: true, zakazka: radek }, 201);
  }

  const radky = await sql`SELECT * FROM zakazky WHERE vlastnik = ${u.email} ORDER BY id`;
  return json({ pocet: radky.length, zakazky: radky });
}

export const config = { path: "/api/zakazky" };
```

Hodnoty vždy přes `${}` v tagované šabloně — driver je parametrizuje. **Nikdy
neskládej SQL spojováním řetězců**, ani u „bezpečně vypadajícího" vstupu.

### Role (jen typ C)

Roli čti z účtu, ne z requestu, a vynuť ji ve funkci:

```js
const ucet = await uzivateleStore().get(u.email, { type: "json" });
if (ucet.role !== "majitel") return json({ chyba: "nemáte oprávnění" }, 403);
```

U dashboardu typu B, kde všichni vidí totéž, role nezaváděj — je to složitost
navíc bez užitku.

## Krok 4 — frontend zůstává statický

**Nepřepínej projekt na SSR kvůli datům.** Statický export a Netlify funkce
fungují vedle sebe — ověřeno. Frontend zůstane rychlý (což je celý důvod, proč
`05-stack.md` volí statický export pro weby) a data obslouží funkce.

`next.config.js` beze změny:

```js
const nextConfig = { output: 'export', images: { unoptimized: true } };
module.exports = nextConfig;
```

`netlify.toml`:

```toml
[build]
  command = "npm run build"
  publish = "out"

[functions]
  directory = "netlify/functions"   # MUSÍ být mimo publish dir
```

Frontend volá vlastní endpointy přes `fetch` a **vždy s `credentials`
nastavenými tak, aby cookie odešla** (u stejné domény to je default). Vzor
přepínače přihlášeno / nepřihlášeno:

```js
const r = await fetch("/api/prihlaseni");
if (r.ok) { /* zobraz aplikaci */ } else { /* zobraz přihlašovací formulář */ }
```

**Data z API nikdy nezapékej do statického buildu** — v `out/` by ležela
veřejně. Všechno chráněné se dotahuje až za běhu po přihlášení.

## Krok 5 — ověř lokálně, než deployuješ

```bash
cd /documents/sites/<slug>
npm install --legacy-peer-deps
chmod +x node_modules/next/dist/bin/next 2>/dev/null || true
netlify dev --offline --port 8899
```

`netlify dev` připojí lokální vývojovou databázi (adresu čti přes `getConnectionString()`, ne z proměnné), takže
Netlify DB se dá vyvíjet **bez provisionování čehokoli v cloudu**. Blobs jedou
v lokálním sandboxu a persistují na disk (`.netlify/blobs-serve/`).

Projeď těchhle šest testů. **Každý musí projít, jinak nedeployuj:**

```bash
# 1. data bez přihlášení → 401
curl -s -o /dev/null -w "%{http_code}\n" localhost:8899/api/zaznamy

# 2. založení účtu bez setup tokenu → 403
curl -s -X POST localhost:8899/api/setup -d '{"email":"a@b.cz"}'

# 3. přihlášení špatným heslem → 401
curl -s -X POST localhost:8899/api/prihlaseni -H 'content-type: application/json' \
     -d '{"email":"test@firma.cz","heslo":"spatne-heslo"}'

# 4. přihlášení správným heslem → 200 + cookie
curl -s -c c.txt -X POST localhost:8899/api/prihlaseni -H 'content-type: application/json' \
     -d '{"email":"test@firma.cz","heslo":"<heslo nastavené přes odkaz>"}'

# 5. podvržený vlastník v těle → uloží se vlastník ze session, ne z requestu
curl -s -b c.txt -X POST localhost:8899/api/zaznamy -H 'content-type: application/json' \
     -d '{"nazev":"X","vlastnik":"nekdo@jiny.cz"}'

# 6. druhý účet nevidí cizí data → {"pocet":0}
curl -s -b c2.txt localhost:8899/api/zaznamy
```

→ **STOP.** Než pošleš cokoli na produkci, ukaž klientovi výsledek testů 1, 5
a 6 jednou větou: *„Bez přihlášení se k datům nedostane nikdo a každý vidí jen
svoje."* Teprve pak deploy.

**7. Brzda na přihlášení drží.** Šestkrát za sebou špatné heslo:

```bash
for i in $(seq 1 6); do
  curl -s -o /dev/null -w "%{http_code} " -X POST localhost:8899/api/prihlaseni \
    -H 'content-type: application/json' -d '{"email":"test@firma.cz","heslo":"spatne-heslo"}'
done; echo
# čekáno: 401 401 401 401 401 429  — šestý pokus už neprojde
```

Potom **správné** heslo ve stejném okně musí taky vrátit 429. Když projde,
brzda tam není a je to P1.

## Krok 6 — publikace

**Statický export a funkce jedou spolu.** Projekt zůstává `output: "export"`,
serverová část žije v `netlify/functions/`. Publisher je nahraje společně
(`deployMode: static-upload+functions`) a v souhrnu vypíše jejich seznam.
Ověřeno naživo 9. 8. 2026: stránka, přihlášení i čtení z databáze fungovaly.

✅ **Náhled s databází funguje** — pokud projekt čte adresu přes
`getConnectionString()`. Netlify mu pro náhled přidělí **izolovanou větev
databáze**, takže klient si aplikaci proklikne na ostrých mechanikách a
cvičných datech. Tohle je jediná správná cesta pro nové projekty.

⚠️ **Výjimka jen pro starší projekty s pevnou proměnnou.** Ty adresu v náhledu
nedostanou (`/api/*` vrací 502), takže publisher se u nich zastaví a vyžádá si
souhlas klienta s publikací rovnou do produkce. Souhlas musí padnout od
klienta; „pokračuj bez čekání" ho nenahrazuje. **Pro nový projekt to není
řešení — přepiš ho na `getConnectionString()`.**

Beze změny oproti běžnému běhu, jen dva kroky navíc:

```bash
python3 <publisherBaseDir>/scripts/netlify_publish.py build       /documents/sites/<slug> --json
python3 <publisherBaseDir>/scripts/netlify_publish.py ensure-site --slug <slug> --dry-run --json
# Existující site: vezmi vrácené siteId a pokračuj. `wouldCreate: true`:
# STOP, popiš dopad a čekej na explicitní schválení klienta; až potom:
python3 <publisherBaseDir>/scripts/netlify_publish.py ensure-site --slug <slug> --confirm-create --json
python3 <publisherBaseDir>/scripts/netlify_publish.py env-set --site-id <id> --key SESSION_SECRET --from-variable CC_SESSION_SECRET --json
python3 <publisherBaseDir>/scripts/netlify_publish.py env-set --site-id <id> --key SETUP_TOKEN    --from-variable CC_SETUP_TOKEN    --json
# BEZ databáze (Blobs, nebo jen formulář): normální náhled ke schválení
python3 <publisherBaseDir>/scripts/netlify_publish.py deploy /documents/sites/<slug> --site-id <id> --json
# Projekt na getConnectionString(): náhled má vlastní větev databáze, jede normálně.
# Starší projekt s pevnou proměnnou: náhled je slepý, publisher se zastaví.
python3 <publisherBaseDir>/scripts/netlify_publish.py deploy /documents/sites/<slug> --site-id <id> --confirm-publish yes --json
```

U Netlify DB `python3 <publisherBaseDir>/scripts/netlify_publish.py db-init --path /documents/sites/<slug>
--confirm-cost yes` **jednou** v projektu (`--path` je povinný; v
netlify-publisheru opravené, `netlify database init` běží bez `--json`).
🛑 Databázi platí klient — bez jeho výslovného souhlasu příkaz nespouštěj,
sám se bez `--confirm-cost yes` zastaví. Náhled přes `--dry-run` (ten souhlas nevyžaduje, nic nezakládá). Adresu databáze si
Netlify vstříkne samo, do `env-set` nepatří.
🛑 **Adresu databáze si nikdy nesestavuj z proměnné.** Použij
`getConnectionString()` z balíčku `@netlify/database`:

```js
import { getConnectionString } from "@netlify/database";
import pg from "pg";

const pool = new pg.Pool({ connectionString: getConnectionString() });
```

Funkce sama pozná prostředí: **produkce dostane ostrou databázi, náhled
izolovanou větev**. Díky tomu si klient aplikaci proklikne na náhledovém
odkazu ještě před spuštěním a testuje se na kopii, ne na ostrých datech.

⚠️ Starší projekty čtou pevnou proměnnou (`NETLIFY_DATABASE_URL`). Publisher
je kvůli zpětné kompatibilitě pozná a zachová se k nim po starém (náhled je
u nich slepý, proto se zeptá na souhlas s publikací do produkce). **Nové
projekty tuhle cestu nepoužívají.**

⚠️ **`identity-enable` nepoužívej** — Netlify Identity nejde zapnout přes CLI
a pro naše přihlášení není potřeba (účty v Blobs, scrypt, podepsaná cookie,
viz výš). Příkaz na to v novém netlify-publisheru rovnou upozorní.

Účty založ **až po deployi** voláním `/api/setup` se `SETUP_TOKEN`.

## Co klient udělá a co udělá agent

| Kdo | Co |
|---|---|
| **Klient** | 1. Vloží `NETLIFY_AUTH_TOKEN` do Control Center (dělá už dnes kvůli publikaci). 2. Řekne, kdo smí dovnitř — e-maily a role. 3. Zajistí přímé bezpečné doručení jednorázových odkazů; uživatelé si hesla volí sami. |
| **Agent** | Všechno ostatní: volba datové cesty, `netlify database init`, generování a nahrání klíčů, kód funkcí, offline/lokální testy, deploy a založení účtů. Bearer odkazy nevkládá do persistovaného chatu ani tasku. |

Klient **nezakládá žádný další účet** a **nikde neklikne** mimo Control Center.
Když to v konkrétním případě neplatí (Identity), řekni mu to dopředu.

## Zákazy

- ❌ Dashboard s firemními čísly bez přihlášení. Nikdy, ani „na rychlo".
- ❌ Ochrana jen skrytím v UI. Endpoint bez kontroly session je veřejný.
- ❌ `vlastnik`, `role`, `user_id` brané z těla requestu nebo z URL.
- ❌ Filtrování cizích dat až v prohlížeči.
- ❌ Heslo uložené jinak než jako hash. Žádný plain text, žádné base64.
- ❌ Porovnávání hashů nebo podpisů přes `===` — vždy `timingSafeEqual`.
- ❌ Cookie bez `HttpOnly` + `Secure` + `SameSite=Strict`.
- ❌ SQL skládané spojováním řetězců.
- ❌ Hodnoty `SESSION_SECRET` / `SETUP_TOKEN` v chatu, logu, `netlify.toml`
  nebo v souboru v projektu.
- ❌ Reset bearer odkaz v persistovaném chatu, tasku, ticketu nebo logu.
- ❌ Tajemství v `netlify.toml` — funkce je odtud stejně nepřečtou.
- ❌ Veřejná registrace, o kterou klient nepožádal.
- ❌ Přepnutí na SSR jen kvůli datům. Statický export + funkce stačí.
- ❌ Mock data z `lib/data.ts` v odevzdaném dashboardu typu B nebo C.
- ❌ Přihlášení na statické stránce typu A, o které nikdo nepožádal.

## Pasti (každá stála reálný běh)

- **`getDatabase()` vrací objekt, ne funkci.** `const { sql } = getDatabase()`.
- **`netlify identity` jako příkaz neexistuje** a `netlify api enableSiteIdentity`
  taky ne. Identity jde zapnout jen ručně v Netlify UI.
- **`netlify database init` nezná `--json`** a nevrací connection string.
- **Blobs `list()` bez opaque `prefix` vrátí všechno všem.** Klíč vždy
  `v1/${tenantKlic(email)}/${id}`, nikdy raw e-mail.
- **Proměnné z `netlify.toml` funkce nevidí.** Vždy `env-set`.
- **Free a Personal databáze usínají po 5 minutách.** První požadavek po pauze
  je pomalý — není to chyba, řekni to klientovi dopředu.
- **Free plán má tvrdý strop 300 kreditů.** Po vyčerpání se web pauzne.
- **Adresář funkcí musí být mimo publish dir**, jinak se nasadí jako statické
  soubory se zdrojovým kódem.

## Kontrolní seznam před odevzdáním

- [ ] Typ projektu určen (A / B / C) a zapsán do `webDNA.md`
- [ ] Typ B nebo C má přihlášení, i když si o něj klient neřekl
- [ ] Typ A nemá přihlášení navíc
- [ ] Datová cesta vybrána (Blobs **nebo** DB, ne obojí) a zdůvodněna
- [ ] U dashboardu nad cizím systémem použit hotový konektor z
      `cs-skills/_lib/connectors/`, ne vlastní volání od nuly
- [ ] Klíče konektoru nahrané po jedné přes `env-set --from-variable`, nikde nejsou v kódu ani
      v `netlify.toml`
- [ ] Plánované obnovení dat (cron) nastavené — jinak se data po prvním
      stažení už neobnoví
- [ ] Žádná mock data v odevzdaném projektu
- [ ] Každý datový endpoint kontroluje session na prvním řádku
- [ ] Vlastník se bere ze session, nikde z requestu
- [ ] Filtr na serveru, ne v prohlížeči
- [ ] Hesla jako scrypt hash, porovnání `timingSafeEqual`
- [ ] Přihlášení má brzdu: 6× špatné heslo vrátí 429, správné heslo v okně taky
- [ ] Účty založené přes jednorázový odkaz; heslo ani bearer odkaz nikde
      v persistovaném chatu, tasku, ticketu nebo logu
- [ ] Cookie má `HttpOnly` + `Secure` + `SameSite=Strict` + `Max-Age`
- [ ] `SESSION_SECRET` a `SETUP_TOKEN` nahrané přes `env-set`, hodnoty nikde nevypsané
- [ ] `.env` v `.gitignore`, v projektu jen `.env.priklad`
- [ ] Všech 7 lokálních testů z kroku 5 prošlo
- [ ] Klientovi ukázán výsledek testů 1, 5 a 6 → STOP → schválení
- [ ] Účty založeny po deployi, přístupy předány
- [ ] Klientovi řečeno, kdy databáze usíná a jaký má plán strop kreditů

---
