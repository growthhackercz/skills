# Landing handoff — reklama ↔ kongruentní landing page

Reklama posílá na `landingUrl`, ale konverze se stane až **na stránce**. Když landing chybí (nebo chceš dedikovanou LP na konkrétní úhel), `ad-strategist` nezablokuje — **vyrobí landing brief a zadá stavbu** vhodnému builderu. Reklamní rodina landing sama nestaví, **řídí** stavbu (stejně jako makery/publishery).

## Princip: message match (congruency is king)
Landing **musí sedět s reklamou** — stejný **slib · hook · úhel · awareness level · persona**. Když reklama slíbí X a stránka mluví Y, návštěvník odskočí (leak). Proto landing brief **vychází z vítězného úhlu**, ne z generické šablony.

## Kdy stavět landing
- `landingUrl` chybí → `blocked_missing_landing_url` **NENÍ konec** → spusť landing handoff.
- Silný úhel na cold awareness (Unaware/Problem-Aware) → často chce **dedikovanou LP** (jiná stránka než bottom-funnel prodejní), aby seděla awareness.
- Lead magnet offer → landing + děkovací stránka.

## Route builderu (skryté před klientem)
```
Klient v CliqSales/GHL?  ANO → GHL AI Studio (in-platform funnel/landing) = DEFAULT
                         NE  → vibe-builder (VibeCoding web) → deploy netlify-publisher
Offer = lead magnet?          → lead-magnet-generator (landing + děkovací stránka)
WordPress trh (cz/com/es)?    → elementor-cliqsales
```
GHL AI Studio je nativní pro platformu (viz pravidlo: agent v platformě = **výhradně GHL AI Studio**, nikdy lovable). `vibe-builder` je standalone (CTO větev).

## `landing-brief.json` (kontrakt do builderu)
Ulož do `/documents/ads/campaigns/{campaign-slug}/`:
```json
{
  "campaignSlug": "…",
  "sourceAngle": {"angle": "…", "hook": "…", "awareness": "problem_aware", "persona": "…"},
  "offer": "…", "promise": "…", "proof": ["…"], "objections": ["…"], "cta": "…",
  "language": "cs",
  "builder": "ghl_ai_studio",
  "reason": "…",
  "sections": ["hero (hook 1:1 s reklamou)", "problém/agitace", "řešení (mechanismus)", "důkaz", "nabídka", "FAQ/námitky", "CTA"],
  "status": "brief",
  "url": null
}
```
`status`: `brief` → `building` → `live` (+ `url`). Sekce = **message-matched skelet** (hero drží stejný hook jako reklama), naplnění je práce builderu z Brand/Product DNA.

## Blokace publikace
Dokud landing nemá **živou `url`**, `ad-plan.json` drží `blocked_missing_landing_url` a publisher **nepublikuje** (kampaň bez cíle = utracený rozpočet). Jakmile builder vrátí `url`, doplň ji do `publishingTargets`/copy a odblokuj.

## Kam to patří v toku
`ad-strategist` Krok 5 (makery) běží paralelně s landing handoffem; **Krok 6 (publisher) čeká na živou landing url**. Learning: konverzní data z landing (přes `ad-analyst` / GA) zpětně skórují úhel — stránka je součást testu úhlu, ne odděleně.
