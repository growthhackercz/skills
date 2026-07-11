# Creative Specs

## Default Output

- Format: JPEG
- Size: 1024 x 1024 px
- Aspect ratio: 1:1
- Quality: medium for generation, high for final review when supported
- Optional upscale: 2000 x 2000 px into `carousel/2000/`

## Required Files

Each finished carousel folder should contain:
- `01-hero.jpg`
- `02-nabidka.jpg`
- `03-social-proof.jpg`
- `04-detail.jpg`
- `05-pred-po.jpg`
- `06-lifestyle.jpg`
- `carousel-manifest.json`

Subsets are allowed when the user explicitly asks for only selected card types. The manifest must reflect the actual generated subset.

## Quality Checklist

Before marking the set done:
- Every file exists and is a bitmap image.
- All generated images have identical dimensions.
- All generated images are exactly 1:1.
- The product remains faithful to the input product photo.
- No copied logo, wordmark, watermark, or corner brand mark appears unless it is physically printed on the product.
- Visible text is in the target language.
- Card 05 is a vertical 50/50 before-after split, with product only on the after side.
- Card 04 shows real visual detail, components, or material/feature objects, not just a text list.
- Cards do not repeat the same person, family, headline, benefit angle, footer, or callout layout.

## Manifest Notes

`actualWidth` and `actualHeight` must match the real pixel dimensions. Do not guess. Use the validation helper before reporting completion.

## Upscale Notes

Upscale is optional and should be offered after approval of the 1024 px set. The helper keeps originals in place and writes enlarged copies into `carousel/2000/`.
