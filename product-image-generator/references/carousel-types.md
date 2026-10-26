# 6 konverzních typů produktových carousel fotek

Ověřený framework Oliver Kenyona / ConversionWise (analýza tisíců DTC/Shopify brandů). **Prompty níže jsou převzaté doslovně** — neparafrázuj je, nezkracuj. Jediná povolená úprava je dosazení `{PRODUCT}` + `{BRAND_CONTEXT}` (viz níž) a rozměr řídí parametr `size`, ne text promptu.

## Jak používat tyto šablony

Každý prompt je **anglický** (GPT image 2 dává v angličtině lepší výsledky). Před generováním do něj dosaď dva placeholdery:

**`{PRODUCT}`** = název + krátký popis reálného produktu z productDNA.
Příklad: „Bioptron MedAll, a Swiss certified medical light-therapy biolamp with a fullerene C60 filter on a stand".

**`{BRAND_CONTEXT}`** = brand mood z brandDNA + věrnost produktu + **zákaz loga** + **čeština**. Vlož ji hned za první větu promptu.
Šablona: „Brand mood: {paleta HEX}, {emoční tón}, {styl fotografií}. Use the attached product photo as the exact, faithful reference for the real product — same shape, proportions, colors and details; do not invent a different product. Render NO brand logo, wordmark, badge or watermark as a graphic overlay — keep only markings physically on the product itself, and do NOT copy any logo from the brand-board reference. All visible text strictly in Czech with correct diacritics. When the card calls for text/graphics (offer, social proof, feature, before/after), use a rich premium editorial layout — strong typographic hierarchy, tasteful labeled callout chips/badges and icon bullets, at the quality of a top-tier DTC brand. Copywriting in a refined premium editorial voice — elegant, confident, modern, benefit-led but understated, like an ad in a high-end lifestyle/design magazine; never hard-sell, discount-flyer or shouty. Typography is modern editorial: clean mixed-case headlines (avoid shouty ALL-CAPS, but keep a confident SEMI-BOLD weight — the main headline must be clearly legible and stand out strongly, never thin, light or faint), generous whitespace, sophisticated hierarchy, tasteful accent color — legible but elegant, never loud or cheap. Avoid aggressive savings/discount claims. NO tiny/mini captions that vanish at thumbnail size. This card must emphasize a DIFFERENT angle and different supporting points than the other cards in the set — never repeat the same headline, claim or benefit list across the carousel. Feature DIFFERENT, visually distinct people on each card (vary age, gender, appearance, household) — never reuse the same person or family across the set; keep only brand style, lighting and the product consistent, NOT the people. Each card has UNIQUE supporting elements — do NOT repeat the same bottom callout strip, icon row or footer from another card. Text sits on subtle, light or translucent panels — NEVER heavy dark blocks covering half the image; let the photography breathe. Keep headlines short and punchy (a few words, max 2–3 lines — do NOT over-set long multi-line headlines) and play with refined, professional typographic contrast (size and weight), like a designer magazine. The PHOTOGRAPHY itself must be bold and premium — rich tonal contrast, depth, dramatic-but-tasteful lighting (never flat or washed-out), magazine-grade; subtle overlays must NOT flatten or dull the image. Vary both the people AND the setting/scene across cards for visual richness and contrast. Keep each card to ONE clear composition — do NOT over-fragment into many mini-panels or a busy collage (NEVER 6-7 separate panels on one image). Hero and Lifestyle are a SINGLE clean photographic image (no multi-panel grids), with minimal supporting text. Detail may show the product plus exploded components, but stays clean and uncluttered — not a panel collage. Fewer, stronger elements beat many small ones."

> Pokud brandDNA chybí, vlož jen generický prémiový tón a vynech barvy (nevymýšlej brand prvky).

**`{ANGLE}`** = pro KAŽDÝ typ **jiný konkrétní úhel z Product DNA** (ne generický). Tím každá karta nese vlastní argument a sada se neopakuje. Mapování typ → odkud v Product DNA čerpat:

| Karta | `{ANGLE}` čerpá z Product DNA |
|---|---|
| 1 Hero | hlavní kýžený **výsledek / transformace** (hlavní slib, emoční „po") |
| 2 Nabídka | konkrétní **nabídka / hodnota** (co klient dostane, balíček, záruka, dárky) |
| 3 Social proof | konkrétní **důkaz důvěry** (certifikace, ocenění, počet zákazníků, klinické testy) |
| 4 Detail | 1 nejsilnější **USP + konkrétní vlastnosti / složení** (klíčové features) |
| 5 Před→po | konkrétní **bolest → úleva** (transformace před→po) |
| 6 Lifestyle | konkrétní **identita / cílovka** (ideální zákazník a jeho hodnoty) |

Každý `{ANGLE}` vyber z JINÉ části Product DNA — 6 karet = 6 různých argumentů, nikdy stejný 2×. Pokud Product DNA chybí, vynech řádek s `{ANGLE}` (nech Kenyonův obecný text).

**Reference (parametr `images` u `image_generate`, max 3, v tomto pořadí):**
1. Fotka produktu (vždy) — drží věrnost reálného produktu.
2. Schválený hero `01-hero.jpg` (u typů 2–6) — style anchor pro konzistenci sady. U pilotního hera místo něj brand-board.
3. Brand-board (pokud existuje).

**Rozměr:** Kenyonův originál říká „2000×2000 / 8K" — to ale řídíme parametrem `size: "1024x1024"` (image_generate `2048²` padá na 5 MB limit). V promptu proto zůstává jen „exact 1:1 square aspect ratio"; konkrétní pixely neřeš textem. Na 2000×2000 se případně upscaluje post-krokem (`scripts/upscale.py`). Viz `creative-specs.md`.

**Text v obrázku:** Nech prompty pracovat. Kenyonovy prompty samy generují review/rating (social proof), feature callouts a ingredience (clarity), před/po labely (transformation) i nabídkový text (offer). **Nepotlačuj text** — je součástí konverzního charakteru karet. **Veškerý viditelný text v jazyce trhu (default čeština), správně s diakritikou — i labely PŘED/PO (ne BEFORE/AFTER).** Technický popis scény anglicky. **Žádné brand logo/wordmark/watermark jako overlay** (jen značení fyzicky na produktu).

---

## 1. Hero — výsledek (`01-hero.jpg`)

**Účel:** Nejdůležitější obrázek na PDP. Ne „tady je produkt", ale „tady je výsledek, který chci". Zastaví scroll. **Proč funguje:** lidé kupují výsledky, ne produkty.

```
Create a premium, ultra high-definition DTC ecommerce hero image for {PRODUCT}.
{BRAND_CONTEXT}
Card angle (from Product DNA, unique to this card — do not reuse on other cards): {ANGLE}
The image should feel like a high-converting Shopify brand product page hero image used by elite modern ecommerce brands.
Focus on the OUTCOME and transformation the customer desires, not just the product itself.
The product must be the clear focal point, beautifully lit, highly detailed, realistic, and naturally integrated into the scene.
Style requirements:
Premium DTC aesthetic
Clean composition
Cinematic lighting
Soft natural shadows
High contrast
Mobile-first composition
Realistic textures
Ultra sharp focus
Minimal clutter
Modern luxury ecommerce feel
High-end advertising photography
Shallow depth of field
Aspirational lifestyle vibe
The image should instantly communicate:
What the product is
Why someone wants it
How it improves their life
Include:
A realistic human interacting naturally with the product if relevant
Emotion and energy
Strong visual hierarchy
Avoid:
Generic stock photo feel
Busy backgrounds
Fake-looking AI hands/faces
Cluttered props
Overdesigned scenes
Multiple focal points
Additional Shopify carousel optimization requirements:
Generate the image in an exact 1:1 square aspect ratio
Design specifically for Shopify product page image carousels
Ensure all six carousel images maintain identical dimensions and composition consistency
Keep all important visual elements centered for mobile-responsive cropping
Maintain a single clear focal point per image
Ensure the product remains instantly recognizable at thumbnail size
Optimize for mobile-first ecommerce viewing
Prioritize fast visual comprehension and conversion clarity
Use premium DTC ecommerce composition standards
Avoid excessive empty space or uneven framing
Maintain consistent lighting, framing quality, realism, and visual polish across the full carousel set
Optimize for sharp zoom functionality on Shopify product pages
Maintain photorealistic ultra high-definition quality
Ensure the image feels consistent with premium modern ecommerce brands
Output style:
Photorealistic, premium ecommerce campaign image, ultra high-definition quality, conversion-focused, suitable for a Shopify product image carousel.
```

---

## 2. Nabídka / hodnota (`02-nabidka.jpg`)

**Účel:** Okamžitě odpoví „proč koupit teď". Nejlepší značky nabídku nezskrývají. **Proč funguje:** jasnost konvertuje. Nabídkový text (2+1, doprava zdarma, záruka…) piš v jazyce trhu.

```
Create a high-converting ecommerce promotional image for {PRODUCT} in a premium DTC brand style.
{BRAND_CONTEXT}
Card angle (from Product DNA, unique to this card — do not reuse on other cards): {ANGLE}
The goal of this image is to instantly communicate a compelling offer or value proposition while maintaining a luxury ecommerce aesthetic.
The product must remain visually dominant while the offer feels bold, clear, and impossible to miss.
Style requirements:
Modern Shopify DTC design aesthetic
Premium ecommerce ad creative
Ultra clean layout
Strong contrast
High readability on mobile
Minimal but impactful composition
Luxury advertising feel
Cinematic lighting
Sharp product detail
Clear visual hierarchy
The image should visually communicate:
Savings
Exclusivity
Urgency
Trust
Simplicity
Examples of offer styles:
Buy 2 Get 1 Free
Limited Time Offer
Save £100 Today
Free Shipping
90-Day Guarantee
Best Seller Bundle
Avoid:
Cheap salesy design
Flashy discount stickers
Cluttered graphics
Too much text
Generic ecommerce templates
Overcrowded layouts
Additional Shopify carousel optimization requirements:
Generate the image in an exact 1:1 square aspect ratio
Design specifically for Shopify product page image carousels
Ensure all six carousel images maintain identical dimensions and composition consistency
Keep all important visual elements centered for mobile-responsive cropping
Maintain a single clear focal point per image
Ensure the product remains instantly recognizable at thumbnail size
Optimize for mobile-first ecommerce viewing
Prioritize fast visual comprehension and conversion clarity
Use premium DTC ecommerce composition standards
Avoid excessive empty space or uneven framing
Maintain consistent lighting, framing quality, realism, and visual polish across the full carousel set
Optimize for sharp zoom functionality on Shopify product pages
Maintain photorealistic ultra high-definition quality
Ensure the image feels consistent with premium modern ecommerce brands
Output style:
Photorealistic premium DTC promotional image, optimized for Shopify ecommerce product carousels, high-converting, ultra high-definition quality.
```

---

## 3. Social proof / důvěra (`03-social-proof.jpg`)

**Účel:** Buduje důvěru — produkt působí milovaně, ověřeně, sociálně potvrzeně. UGC styl poráží naleštěnou korporátní kreativu. **Proč funguje:** lidé věří lidem, ne značkám.

```
Create a premium ecommerce trust-building image for {PRODUCT} designed for a high-converting Shopify product page carousel.
{BRAND_CONTEXT}
Card angle (from Product DNA, unique to this card — do not reuse on other cards): {ANGLE}
The goal is to make the brand feel credible, trusted, loved, and socially validated.
The image should feel authentic, human, and emotionally believable rather than overproduced.
Style requirements:
Premium user-generated content aesthetic
Realistic lifestyle photography
Natural lighting
Human emotion and authenticity
High-end DTC brand feel
Modern ecommerce composition
Clean visual hierarchy
Ultra realistic skin textures and product detail
Slightly candid photography feel
Social-proof-driven composition
Include:
Realistic happy customers using the product naturally
Diverse representation if relevant
Genuine emotional expressions
Optional review/rating integration
Optional press-style credibility integration
Mobile-first framing
The image should visually communicate:
Trust
Community
Credibility
Popularity
Customer satisfaction
Avoid:
Fake-looking influencer aesthetics
Overly posed stock photography
Heavy filters
Unrealistic perfection
Cluttered testimonial graphics
Cheap review badge styling
Additional Shopify carousel optimization requirements:
Generate the image in an exact 1:1 square aspect ratio
Design specifically for Shopify product page image carousels
Ensure all six carousel images maintain identical dimensions and composition consistency
Keep all important visual elements centered for mobile-responsive cropping
Maintain a single clear focal point per image
Ensure the product remains instantly recognizable at thumbnail size
Optimize for mobile-first ecommerce viewing
Prioritize fast visual comprehension and conversion clarity
Use premium DTC ecommerce composition standards
Avoid excessive empty space or uneven framing
Maintain consistent lighting, framing quality, realism, and visual polish across the full carousel set
Optimize for sharp zoom functionality on Shopify product pages
Maintain photorealistic ultra high-definition quality
Ensure the image feels consistent with premium modern ecommerce brands
Output style:
Photorealistic premium DTC trust image, emotionally convincing, highly realistic, suitable for Shopify product image carousels.
```

---

## 4. Detail / vlastnosti (`04-detail.jpg`)

**Účel:** Odstraňuje tření — vizuálně odpoví „co přesně kupuji". **Proč funguje:** snazší pochopení = snazší nákup. Callouty / ingredience / složení v jazyce trhu.

```
Create a premium ecommerce product feature image for {PRODUCT} designed to maximize product understanding and reduce purchase hesitation.
{BRAND_CONTEXT}
Card angle (from Product DNA, unique to this card — do not reuse on other cards): {ANGLE}
The goal is to make the product feel crystal clear, premium, easy to understand, and highly valuable.
The product must be beautifully displayed with strong emphasis on materials, features, craftsmanship, ingredients, texture, or included components.
Style requirements:
Apple-style product photography
Minimalist premium DTC aesthetic
Ultra clean background
Soft cinematic lighting
Hyper detailed textures
Sharp focus
High-end commercial photography
Elegant composition
Mobile-first readability
Luxury ecommerce presentation
Include:
Close-up detail shots
Feature callout areas
Ingredient/material visibility if relevant
Exploded-view composition OR the product's key components / filtration stages laid out as distinct physical elements around the product (show what's inside — like a premium clarity image with ingredients/parts spread out, NOT just a text list)
Optional packaging / what's-in-the-box layout
Strong visual clarity
The image should visually communicate:
Quality
Simplicity
Premium craftsmanship
Transparency
Ease of understanding
Avoid:
Busy infographic design
Technical overload
Cheap Amazon-style layouts
Excessive icons
Cluttered text
Distracting props
Additional Shopify carousel optimization requirements:
Generate the image in an exact 1:1 square aspect ratio
Design specifically for Shopify product page image carousels
Ensure all six carousel images maintain identical dimensions and composition consistency
Keep all important visual elements centered for mobile-responsive cropping
Maintain a single clear focal point per image
Ensure the product remains instantly recognizable at thumbnail size
Optimize for mobile-first ecommerce viewing
Prioritize fast visual comprehension and conversion clarity
Use premium DTC ecommerce composition standards
Avoid excessive empty space or uneven framing
Maintain consistent lighting, framing quality, realism, and visual polish across the full carousel set
Optimize for sharp zoom functionality on Shopify product pages
Maintain photorealistic ultra high-definition quality
Ensure the image feels consistent with premium modern ecommerce brands
Output style:
Photorealistic premium ecommerce product feature image, highly detailed, luxury DTC brand quality, optimized for conversion and product clarity.
```

---

## 5. Problém → řešení / transformace (`05-pred-po.jpg`)

**Účel:** Emoční kontrast — ukáže bolest a pak transformaci. Funguje u wellness, beauty, doplňků, fitness, péče o pleť, gadgetů. **Proč funguje:** lidé kupují pohyb ze současného do kýženého stavu.

```
Create a high-converting ecommerce transformation image for {PRODUCT} designed around a clear problem-to-solution narrative.
{BRAND_CONTEXT}
Card angle (from Product DNA, unique to this card — do not reuse on other cards): {ANGLE}
The image should visually dramatize the difference between the customer's painful current state and their improved desired outcome after using the product.
The transformation should feel emotionally powerful, visually obvious, and believable.
Style requirements:
Premium DTC advertising aesthetic
Cinematic storytelling
Strong emotional contrast
Clean composition
High realism
Ultra sharp product detail
Dramatic but tasteful lighting
Mobile-first visual clarity
Luxury ecommerce feel
Structure:
Compose as an EXACT 50/50 vertical split — BEFORE on the left half, AFTER on the right half, both occupying equal area and equally prominent (never let one side dominate)
The product appears ONLY in the AFTER half — NEVER in the BEFORE half (BEFORE = the problem / old state WITHOUT the product; AFTER = the product as the solution)
Visually show BEFORE vs AFTER
Strong emotional difference between both states
Product integrated naturally as the solution
Clear transformation without needing heavy text
The image should visually communicate:
Relief
Improvement
Confidence
Simplicity
Positive transformation
Examples:
Tired vs energized
Messy vs organized
Dry skin vs glowing skin
Frustrated vs confident
Low energy vs active lifestyle
Avoid:
Fake exaggerated transformations
Medical-looking graphics
Aggressive red arrows/circles
Cheap before/after aesthetics
Unrealistic body transformations
Cluttered layouts
Additional Shopify carousel optimization requirements:
Generate the image in an exact 1:1 square aspect ratio
Design specifically for Shopify product page image carousels
Ensure all six carousel images maintain identical dimensions and composition consistency
Keep all important visual elements centered for mobile-responsive cropping
Maintain a single clear focal point per image
Ensure the product remains instantly recognizable at thumbnail size
Optimize for mobile-first ecommerce viewing
Prioritize fast visual comprehension and conversion clarity
Use premium DTC ecommerce composition standards
Avoid excessive empty space or uneven framing
Maintain consistent lighting, framing quality, realism, and visual polish across the full carousel set
Optimize for sharp zoom functionality on Shopify product pages
Maintain photorealistic ultra high-definition quality
Ensure the image feels consistent with premium modern ecommerce brands
Output style:
Photorealistic premium DTC transformation image, emotionally persuasive, highly believable, optimized for Shopify ecommerce product carousels.
```

---

## 6. Lifestyle / identita (`06-lifestyle.jpg`)

**Účel:** Prodává identitu, ne jen produkt. „Takový člověk chci být." **Proč funguje:** identita je jedna z nejsilnějších konverzních pák.

```
Create a premium lifestyle ecommerce image for {PRODUCT} designed to build aspiration, identity, and emotional brand connection.
{BRAND_CONTEXT}
Card angle (from Product DNA, unique to this card — do not reuse on other cards): {ANGLE}
The image should feel like a luxury DTC campaign from a top-tier Shopify brand.
The product should be naturally integrated into an aspirational lifestyle scene that reflects the identity the customer wants to associate with.
Style requirements:
Cinematic lifestyle photography
Premium luxury DTC aesthetic
Editorial-quality composition
Natural lighting
Sophisticated color grading
Emotionally rich atmosphere
Modern aspirational branding
Clean composition
High realism
Ultra high-definition detail
Mobile-first framing
The image should visually communicate:
Status
Identity
Lifestyle upgrade
Taste
Belonging
Aspiration
Include:
Beautiful real-world environments
Natural human interaction
Authentic emotion
Subtle luxury cues
Strong visual storytelling
The overall feeling should be:
"This is the type of person I want to be."
Avoid:
Overly staged influencer poses
Generic stock photography
Cluttered environments
Unrealistic AI aesthetics
Overediting
Multiple competing focal points
Additional Shopify carousel optimization requirements:
Generate the image in an exact 1:1 square aspect ratio
Design specifically for Shopify product page image carousels
Ensure all six carousel images maintain identical dimensions and composition consistency
Keep all important visual elements centered for mobile-responsive cropping
Maintain a single clear focal point per image
Ensure the product remains instantly recognizable at thumbnail size
Optimize for mobile-first ecommerce viewing
Prioritize fast visual comprehension and conversion clarity
Use premium DTC ecommerce composition standards
Avoid excessive empty space or uneven framing
Maintain consistent lighting, framing quality, realism, and visual polish across the full carousel set
Optimize for sharp zoom functionality on Shopify product pages
Maintain photorealistic ultra high-definition quality
Ensure the image feels consistent with premium modern ecommerce brands
Output style:
Photorealistic luxury DTC lifestyle campaign image, premium ecommerce quality, emotionally aspirational, suitable for Shopify product image carousels.
```
