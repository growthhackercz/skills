---
name: image-generation
description: "Generuje obrázky (plné portréty a ikony) pro AI CEO hlavního agenta using Nanobana 2 + Gemini Flash 3.1; ukládá prompty a výstupy do ~/documents. Podporuje více variant a formátů."
category: Ads & Creative
---

# Image Generation

## Overview
This skill enables direct image generation using Nanobana 2 and Gemini Flash 3.1, producing a full portrait and an icon for the AI CEO of the main agent. Outputs and prompts are stored under ~/documents and in the skill's workspace assets for reuse.

## Prerekvizity
- Nanobana 2 integrated access
- Gemini Flash 3.1 available
- OpenRouter API accessible (auth token configured)
- Práva k zápisu do ~/documents

## Workflow
1. Define target formats and sizes ( portrait 3000x4000 PNG, icon 512x512 SVG/PNG )
2. Choose styles (realistic vs stylized; nanobana2) and color spectrum (blue, cyber-silver, cyan)
3. Create two prompts (portrait, icon) in prompts/ with notes
4. Generate assets via Nanobana 2 / Gemini Flash 3.1
5. Save outputs to ~/documents/ai-ceo-assets and commit prompts/README
6. Optional: package into a .skill for distribution

## Prompts
- See prompts.md for two ready-to-use prompts with usage notes

## Outputs & Formats
- Portrait: PNG 3000x4000
- Icon: SVG (preferred) or PNG 512x512
- Variants: 1–2 alternate styles (additional prompts)

## Licensing & Usage
- Ensure rights for commercial use of generated visuals.

## Packaging
- If needed, scripts to package as .skill and CI integration notes.
