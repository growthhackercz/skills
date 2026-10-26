# Čtení Sales DNA — které sekce a jak

Sales Assistant čte z `/documents/sales/salesDNA.md`. Nekopíruj celý soubor do kontextu — čti cíleně sekce podle režimu.

| Sekce | Kdy | Co z ní bereš |
|---|---|---|
| **§1 Nastavení enginu** | vždy | tým ano/ne, mapping obchodník → GHL user (pro `--assignee`), pracovní doba, trh, režim funnelů |
| **§3 Produkty a ceny** | příprava, po hovoru | kotva (hodnota → cena), pořadí prezentace (VŽDY hodnota před cenou), pravidlo slev, per produkt |
| **§4 Prodejní metodika** | příprava | struktura schůzky (kroky), klíčové otázky, signature techniky (např. Zrcadlo), čemu se vyhnout |
| **§5 Námitky a odpovědi** | příprava, po hovoru | battlecards — vyber jen ty, co u TOHOTO kontaktu reálně hrozí |
| **§8 Mapa pipelines** | hygiena, po hovoru | do které pipeline patří deal, pravděpodobnosti fází, co je „mimo engine" |

## Pravidla

- **Kotvy a ceny VŽDY z §3, nikdy z hlavy.** Když §3 hodnotu nemá, napiš „kotva neurčena — doplňte §3", nevymýšlej číslo.
- **Metodiku ber z §4 klienta**, nevymýšlej vlastní strukturu schůzky.
- **Per produkt:** má-li klient víc produktů, §3/§5 mají podsekce `### <produkt>` — použij tu, která sedí na fit.
- Když salesDNA neexistuje → STOP (doporuč `sales-dna-generator`), nezačínej improvizovat.
- **Mapping obchodníků (§1):** když chybí, task action do plánu nepřidávej. Upozorni „mapping obchodník → CRM uživatel v §1 chybí" a vyžádej jeho doplnění; `ghl_assistant_push.py` bez neprázdného `--assignee` selže před zmrazením plánu.
