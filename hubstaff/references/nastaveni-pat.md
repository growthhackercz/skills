# Nastavení Hubstaff Personal Access Tokenu (PAT)

Aby agent mohl číst data z vašeho Hubstaff účtu, potřebuje **Personal Access Token (PAT)**. Je to dlouhý řetězec, který Hubstaff vygeneruje vám osobně. Token funguje jako klíč — agent ho přiloží ke každému požadavku, Hubstaff podle něj pozná, kdo se ptá, a vrátí pouze data, na která máte oprávnění.

Token se nastavuje **jednorázově**. Pak ho agent může používat dlouhodobě (vnitřně se sám obnovuje).

## Krok 1 — Přihlaste se do Hubstaffu

Otevřete <https://app.hubstaff.com> a přihlaste se účtem, který má přístup k datům, která chcete agentovi zpřístupnit (typicky účet **majitele** nebo **manažera s plnými právy** — token bude mít stejná oprávnění jako vy).

## Krok 2 — Otevřete stránku Personal Access Tokens

V pravém horním rohu klikněte na své jméno → **Account settings**. V levém menu najděte **Personal Access Tokens** (případně **API & integrations** → **Personal Access Tokens**).

Přímý odkaz: <https://app.hubstaff.com/account/personal_access_tokens>

## Krok 3 — Vytvořte nový token

1. Klikněte na **Create token** (nebo **Generate new token**).
2. Pojmenujte token tak, aby bylo jasné, kde běží — např. `CliqSales AI Tým`.
3. Vyberte **organizaci** nebo organizace, pro které má token platit.
4. (Volitelně) Zvolte rozsah oprávnění — pro plné monitorování zaměstnanců zvolte **všechna oprávnění pro čtení** (read all). Pokud chcete agentovi zpřístupnit jen některé části, omezte.
5. Klikněte **Create**.

Hubstaff vám zobrazí token. **Zkopírujte si ho hned** — po zavření okna ho už znovu neuvidíte (museli byste vygenerovat nový).

## Krok 4 — Nastavte token do prostředí agenta

Token agent čte z proměnné prostředí `HUBSTAFF_PAT`. Postup závisí na tom, kde běží:

### Pokud máte CliqSales AI Tým (běžný klient)

Přidejte token do správce tajemství vašeho workspace:

1. Otevřete CliqSales Control Center vašeho účtu.
2. V administraci najděte sekci **Tajemství / API klíče**.
3. Přidejte nový záznam:
   - **Jméno:** `HUBSTAFF_PAT`
   - **Hodnota:** vámi zkopírovaný token
4. Uložte. Agent ho automaticky vyzvedne při dalším spuštění.

### Pokud spouštíte skill ručně přes terminál (dev / pokročilý uživatel)

Přidejte do `~/.bashrc` nebo `~/.zshrc`:

```bash
export HUBSTAFF_PAT="váš-token-sem"
```

A znovu otevřete terminál (nebo spusťte `source ~/.bashrc`).

## Krok 5 — Ověřte, že to funguje

Požádejte agenta: **„Hubstaff — kdo jsem?"**

Agent zavolá ověřovací příkaz a vrátí vaši identitu a ID organizace. Pokud uvidíte něco jako:

> Přihlášen jako jan.novak@firma.cz (Jan Novák). Výchozí organizace ID: 123456.

Token je v pořádku.

## Co dělat, když token přestane fungovat

Hubstaff token sám o sobě nevyprší (může běžet roky), ale **přestane platit, když:**

- ho v Hubstaffu **smažete** (Account → Personal Access Tokens → Revoke)
- **změníte své heslo nebo email** (Hubstaff může pro jistotu zneplatnit aktivní tokeny)
- **odeberete si role v organizaci** (token ztratí přístup k datům, na která už nemáte právo)

Pokud agent začne hlásit `Chyba: Výměna tokenu selhala (HTTP 401)`, vygenerujte nový token (Krok 3) a přepište proměnnou `HUBSTAFF_PAT` (Krok 4).

## Bezpečnostní poznámka

Token je **stejně citlivý jako vaše heslo do Hubstaffu**. Kdokoli ho získá, může číst data o vašem týmu. Proto:

- Nikdy ho neukládejte do Gitu / veřejných souborů.
- Nikdy ho neposílejte e-mailem / Slackem nešifrovaně.
- Nikdy ho neukazujte na sdílené obrazovce.
- Pokud máte podezření, že unikl — okamžitě ho v Hubstaffu zneplatněte (**Revoke**) a vygenerujte nový.
