# Pointer-poznámka na kartu klienta

Krátká poznámka, kterou Mentor přidá ke kontaktu klienta (jen když §1 „Hodnocení hovorů na kartu klienta" = zapnuto). **NE celý scorecard** — jen skóre + odkaz na detail v Data Center. Plný scorecard žije v `/documents/sales/scorecards/<obchodník>/`.

## Formát (první řádek = název, GHL nezobrazuje titulek poznámky)
```
## 📊 Prodejní hodnocení - obchodník <jméno> - <datum>
Skóre **<X> %** · nejsilnější: <kategorie> · ke zlepšení: <jedna věc jednou větou>
Detail hodnocení: /documents/sales/scorecards/<obchodník-slug>/<datum>-<firma-slug>-<callId>/<datum>-<firma-slug>-<callId>-detail.md
```

## Zásady
- Max ~3 řádky. Je to rozcestník, ne hodnocení.
- **Vykání** vůči čtenáři.
- Neuváděj tvrdou kritiku obchodníka do poznámky na klientově kartě (privacy) — jen skóre + neutrální „ke zlepšení". Ostrá zpětná vazba patří do karty pro obchodníka a do Data Center.
- Aditivní tag kontaktu: `sales mentor` (`deliver.py` jej vloží jako závislou action do stejného zmrazeného plánu).
- Když §1 toggle = vypnuto → pointer NEPÍŠEŠ, hodnocení zůstává jen v Data Center.
