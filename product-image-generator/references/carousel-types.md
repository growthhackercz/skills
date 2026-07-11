# Product Carousel Types

Use these six prompt templates without shortening them. Replace `{PRODUCT}`, `{BRAND_CONTEXT}`, `{ANGLE}`, and `{LANGUAGE}` before calling `image_generate`.

Global constraints for every image:
- Preserve the exact physical product from the reference photo: shape, color, material, proportions, markings on the product body.
- Do not invent a different product, packaging, logo, or colorway.
- Do not copy any logo, wordmark, watermark, or corner branding from references. Product markings physically printed on the product are allowed.
- Keep the composition premium, editorial, modern, and clean. Avoid hard-sell retail flyer design.
- Use visible text only when the type requires it. Visible text must be in `{LANGUAGE}`.
- Create one strong composition, not a collage of many small panels.
- Use modern editorial typography: readable semibold headline, mixed-case, short lines, no tiny captions.

## Angle Mapping

When product DNA is available, select a different angle for every card:
- Hero: desired end result or transformation.
- Offer: strongest commercial value without cheap discount energy.
- Social proof: trust driver, user outcome, objection removal.
- Detail: product mechanism, material, ingredient, component, filter stage, or technical differentiator.
- Before/after: problem state before product and solved state after product.
- Lifestyle: identity, aspiration, belonging, or daily-life context.

No two cards may repeat the same headline, claim, benefit list, footer, or supporting visual motif.

## 01 Hero - Result

Photorealistic premium editorial product image for `{PRODUCT}`. Show the product as the hero object inside a clean aspirational scene that communicates the desired result, not just the object. Angle: `{ANGLE}`.

Use the provided product photo as the source of truth. Keep the product faithful 1:1. Premium lifestyle magazine lighting, soft natural contrast, refined color grading aligned with `{BRAND_CONTEXT}`. The scene should feel calm, confident, valuable, and conversion-oriented for an e-commerce product page.

Minimal or no overlay text. If text is used, keep it subtle, readable, and in `{LANGUAGE}`. Do not add any logo, wordmark, watermark, or copied brand mark from references.

## 02 Offer - Value

Photorealistic premium e-commerce carousel image for `{PRODUCT}` focused on offer and perceived value. Angle: `{ANGLE}`.

Use the provided product photo as the source of truth. Keep product shape, color, and physical details faithful. Build a refined editorial offer composition with the product clearly visible, elegant spacing, premium lighting, and a soft panel or typographic system for the offer.

Create concise visible offer copy in `{LANGUAGE}`. The offer must feel premium and benefit-led, not loud, cheap, or sale-bin. Avoid aggressive discount claims unless product DNA explicitly contains them. Do not add any logo, wordmark, watermark, or copied brand mark from references.

## 03 Social Proof - Trust

Photorealistic UGC-inspired but premium carousel image for `{PRODUCT}` focused on social proof and trust. Angle: `{ANGLE}`.

Use the provided product photo as the source of truth. Keep the product faithful 1:1 and clearly present. Show satisfied customers or a believable customer context. If a hero style anchor is provided, match its light, color grading, and product fidelity, but use visually different people from other cards.

Include tasteful visible social proof elements in `{LANGUAGE}`: star rating, one short review quote, or trust cue. Keep typography clean and readable. Avoid overloading the image with many review boxes. Do not add any logo, wordmark, watermark, or copied brand mark from references.

## 04 Detail - Features

Photorealistic premium product detail image for `{PRODUCT}` focused on physical features, materials, components, ingredients, or mechanism. Angle: `{ANGLE}`.

Use the provided product photo as the source of truth. Keep the product faithful 1:1. Create an Apple-style clean detail composition. If relevant, show exploded product components, filter stages, ingredients, or material details as physical objects around the product, not only as text.

Include concise callouts in `{LANGUAGE}` only where they help comprehension. Use clean lines, subtle panels, and readable typography. Do not add any logo, wordmark, watermark, or copied brand mark from references.

## 05 Before After - Transformation

Photorealistic premium before-and-after carousel image for `{PRODUCT}`. Angle: `{ANGLE}`.

Create a precise 50/50 vertical split composition. Left side is the problem state before using the product. Right side is the improved state after using the product. The product appears only on the AFTER side, never on the BEFORE side. Use the provided product photo as the source of truth and keep the product faithful 1:1.

Visible labels must be in `{LANGUAGE}`. For Czech, use `PŘEDTÍM` and `POTOM`; do not use English labels. Keep the visual contrast emotional and clear, but premium, not exaggerated. Do not add any logo, wordmark, watermark, or copied brand mark from references.

## 06 Lifestyle - Identity

Photorealistic premium lifestyle image for `{PRODUCT}` focused on aspiration and identity. Angle: `{ANGLE}`.

Use the provided product photo as the source of truth. Keep the product faithful 1:1. Show the product naturally integrated into the life of the target audience. The viewer should feel "this is the kind of person or home I want to be." Match `{BRAND_CONTEXT}` through color, tone, lighting, and composition.

Use a visually different person, household, age range, and setting than the other cards. Minimal or no overlay text. Do not add any logo, wordmark, watermark, or copied brand mark from references.
