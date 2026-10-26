# Storyboard (GPT Image 2) — koncept + reference stills

Před animací vyrob **storyboard stilly** ve zvoleném stylu. Slouží 2 účely: (1) vizuální schválení směru, (2) **reference-to-video vstup pro Seedance** (Krok 3). Co je na stillu, to Seedance rozanimuje — styl + postava + prostředí musí sedět už tady.

## Story-arc rámce dle typu videa

Příběh **odvoď z brand + product DNA + cíle**. Vyber rámec podle typu, naplň ho konkrétním produktem. Délka určí počet scén (1 scéna ≈ 1 klip ≈ 15 s).

| Typ videa | Rámec (scéna po scéně) |
|---|---|
| **Reklama / promo** | Problém/touha diváka → produkt jako řešení → výsledek/proměna (POV diváka, ne výčet funkcí) |
| **Launch / reveal** | Teaser/napětí → odhalení produktu → klíčová hodnota → CTA |
| **Explainer** | Otázka/„jak na to" → produkt v akci krok za krokem → payoff |
| **Brand story** | Svět/hodnota značky → moment proměny → kým se divák stane |
| **Feature highlight** | Konkrétní bolest → jedna feature ji řeší → before/after |

Nejsi vázaný na tabulku — když koncept dává smysl jinak, použij vlastní oblouk. Vždy: **jeden jasný message**, divák jako hrdina (u sales), payoff na konci.

> **Příklad (první výroba, ai-marketer):** reklamní rámec — podnikatel ve stresu (chybí čas/marketér) → napíše požadavek AI týmu → tým vyrábí a předává si kampaň → hotová multikanálová kampaň → jeho výsledek („vyprodáno", graf nahoru). To je *jeden* příklad naplnění rámce „Reklama", ne povinná šablona.

## Engine

- **GPT Image 2** (`fal-ai/gpt-image-2/edit`, FAL, varianta `/edit` — **BEZ `openai/`**, jinak 404). Pro konzistenci dalších scén dej **předchozí schválený still** (a případně produktovou fotku) jako `image_urls` referenci — HTTPS URL z FAL CDN, **ne data URL** (drží postavu i reálný produkt).
- GPT Image 2 text **umí** — ale tady ho nechceme (`no text, no captions`).
- Pomalé geny → `queue.fal.run` + polling. `image_size` MUSÍ být **preset string** (`landscape_16_9`, `square_hd`, …) — **ne `{width,height}` dict**, jinak 422.

## Pravidla

- **Styl deskriptor** z `styles.md` na začátek promptu (stejný pro všechny stilly).
- **Konzistence postavy/prostředí** — popiš postavu detailně a drž ji; scény 2+ s referencí scény 1.
- **Reálné výstupy, ne nápisy** — co se má na materiálech objevit, popiš jako vizuál (fotka, plocha, graf), ne text (komolil by se a stejně ho překryje overlay).
- **Face-light** — postava ne v extrémním detailu obličeje (Seedance moderace, viz `seedance.md`).
- **Omni mode navíc:** vygeneruj **kanonické čelní portréty postav** (výrazně odlišné — věk / vlasy / oblečení) jako character-lock referenci do každé Omni scény. Viz `omni.md`.
- **`--dry-run`** prompty + cena (~$0.03–0.10/still) + STOP. Ukládej do `_storyboard/`.

Hotový kód: `scripts/gen_storyboard.py`.
