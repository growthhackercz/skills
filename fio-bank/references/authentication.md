# FIO API — Autentizace a token

## Princip

FIO API nepoužívá OAuth, ani API key v hlavičce. Místo toho:

- Klient si v Internetbankingu (IB) vygeneruje **API token** — náhodný string ~64 znaků.
- Token se vkládá **přímo do URL path** každého requestu.
- FIO podle tokenu identifikuje účet a oprávnění.

> Důsledek: token v URL může skončit v access logu, v `ps`, v shell historii. Ukládej ho přes Control Center integraci FIO a používej helper `scripts/fio_get.py`, který si ho dosadí interně (ne přes argv).

## Generování tokenu (návod pro klienta)

Klient (uživatel) sám v IB FIO:

1. Přihlásí se do **Internetbankingu FIO** (ib.fio.cz).
2. Menu **Nastavení** → **API**.
3. Klikne **Vytvořit nový token**.
4. **Nastaví oprávnění** — POVINNĚ zaškrtne **pouze „čtení"** (žádné „odesílání plateb").
5. **Volitelně omezí IP adresou** — doporučeno na IP klientského VPS, kde běží openclaw kontejner.
6. **Volitelně omezí platnost** — defaultně 180 dní, lze zkrátit.
7. Token zkopíruje a uloží **bezpečně** (zobrazí se jen jednou).
8. Token vloží do **Control Center → Integrace → FIO Bank** jako profil účtu. Pokud má víc účtů, založí jeden profil per účet a dá jim jednoznačné názvy, například `hlavni-czk`, `rezervni-czk`, `eur`.

## Doba platnosti a rotace

- **Default platnost: 180 dní** (lze zkrátit při generování).
- Po expiraci API vrací **HTTP 401**.
- Rotace: klient vygeneruje nový token, starý smaže v IB a aktualizuje příslušný FIO profil v Control Center.

**Proaktivní upozornění:**
Pokud agent dostane 401, **nepokoušej se token „opravit" nebo guessovat**. Řekni uživateli, že token vypršel a musí ho vygenerovat znovu (návod výše).

## Read-only vs full token

| Token type | Povoleno | Skill `fio-bank` |
|---|---|---|
| **Read-only** | GET pohybů, výpisy, zarážky | ✅ Pouze tento typ |
| **Plný (read + import plateb)** | Vše + POST `/import/` | ❌ Skill ho nepoužívá ani nepodporuje |

Pokud klient nedopatřením nastaví plný token, skill funguje stejně (volá jen GET endpointy). Ale **doporučení**: požádej klienta o read-only token, snižuje to risk přístup útočníka při leaknutí.

## Bezpečnost

- **NIKDY** token nelogovat (print, error message, traceback s URL).
- **NIKDY** token nedávat do output JSON souboru (ani jako součást URL hlavičky responsu).
- **NIKDY** token nepoužívat v `curl` přes argv pokud existuje alternativa přes helper — argv je viditelné přes `ps aux`.
- Helper `scripts/fio_get.py` token nikde nevypisuje. Pokud potřebuješ debugovat URL, používej `--debug` flag, který tokenovou část v URL maskuje jako `{TOKEN}`.

## Co dělat, když token leaknul

1. Okamžitě v IB FIO → **Nastavení → API → smazat token**.
2. Vygenerovat nový.
3. Zkontrolovat audit log v IB FIO (přístupy k API).
4. Aktualizovat příslušný FIO profil v Control Center.
5. Spustit novou agent session, aby běžela s aktuálním credential snapshotem.

## Co tokenem **nemůžeš**

- Token je **vázán na účet**, ke kterému byl vygenerován. Nelze jím přistupovat k jiným účtům klienta (i kdyby měl víc účtů ve FIO — pro každý potřebuje samostatný token).
- Token **neumožňuje přihlášení do IB**, jen API přístup.
- Token **nelze obnovit** — po expiraci nebo smazání je potřeba vygenerovat nový.
