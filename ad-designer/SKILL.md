---
name: ad-designer
description: Generate image ad creatives using OpenRouter (Gemini Flash Image). Creates Meta/social ad images for campaigns based on brand guidelines and creative briefs.
category: Ads & Creative
---

# Ad Designer

Generate professional image ad creatives for Meta/social campaigns using AI image generation via OpenRouter.

## Model

**Gemini 3.1 Flash Image** (`google/gemini-3.1-flash-image-preview`) via OpenRouter
- Fast, cost-effective image generation (~$0.07/image)
- Good text rendering for ad copy
- Supports multiple aspect ratios
- No separate API key needed — uses your OpenRouter key

## Prerequisites

- OpenRouter API key (already configured in OpenClaw)
- Brand guidelines (colors, fonts, voice) — ideally from shared documents/wiki brand material; structured `brand:*` notes are only a quick fallback
- Creative brief (ad concept, copy, target audience)

## Aspect Ratios

Always specify aspect ratio in the prompt. Common Meta ad formats:

| Ratio | Dimensions | Use Case | Prompt Keyword |
|-------|------------|----------|----------------|
| 1:1 | 1080x1080 | Feed (universal) | "square image" |
| 4:5 | 1080x1350 | Feed (recommended) | "4:5 vertical image" |
| 9:16 | 1080x1920 | Stories/Reels | "9:16 vertical image" |
| 16:9 | 1920x1080 | Landscape | "16:9 landscape image" |

**Default to 1:1** unless brief specifies otherwise — it works everywhere.

## Prompt Engineering

### Critical Rules

1. **Be explicit about exclusions:**
   ```
   NO logos. NO brand names. NO company names. NO watermarks. NO additional text.
   ```

2. **Specify exact text:**
   ```
   The ONLY text on the image should be exactly: [your text here]
   ```

3. **Keep prompts focused:**
   - Don't overload with too many instructions
   - Separate layout from content from style

4. **Include aspect ratio:**
   ```
   Generate a square 1:1 image...
   ```

### Prompt Template

```
Generate a [aspect ratio] image.

[Background/setting description]

[Text content - be explicit:]
The ONLY text should be exactly:
- Line 1: "[text]" in [color] [size]
- Line 2: "[text]" in [color] [size]

[Visual elements - icons, mockups, etc.]

Style: [clean/minimal/warm/professional/etc.]

NO logos. NO brand names. NO watermarks. NO additional elements.
```

### Example Prompts

**Price Anchor Ad:**
```
Generate a square image. White background. Clean typography only, no decorations, no logos, no icons, no borders, no frames.

The ONLY text on the image should be exactly:
Line 1 (small gray): What companies pay €10,000 to train their teams...
Line 2 (large navy blue): You can learn for €249
Line 3 (small gray): AI Operator Course — 10 hours to AI proficiency.

The €249 should be in gold/yellow color. Nothing else. No brand names. No additional elements.
```

**Native/Organic Creative:**
```
Generate a square photograph of a notebook page. Warm lighting. Cream colored lined paper.

Handwritten text in black ink pen that says EXACTLY:
The AI tools dont matter.
The workflows do.
Most people chase the next tool.
Operators master the fundamentals.

Draw a hand-drawn red circle around the word workflows. Coffee cup visible at edge.

NO logos. NO brand names. NO watermarks. Just the notebook with handwritten text.
```

## API Usage

Use the OpenRouter wrapper script — it makes the API call and automatically reports cost to Control Center:

```bash
RESPONSE=$(~/.openclaw/cs-skills/_lib/openrouter-call.sh \
  --model "google/gemini-3.1-flash-image-preview" \
  --agent "$AGENT_NAME" \
  --prompt "YOUR_PROMPT_HERE")
```

The `--agent` flag must be your agent name (e.g. `cmo`, `cso`). This is used for cost attribution.

**Response format:** The generated image is returned in `choices[0].message.images[]` as a base64-encoded data URI (e.g. `data:image/png;base64,...`). The `message.content` field may be `null` — always check the `images` array.

**Extracting the image:**
```bash
# Save the base64 image from the response
echo "$RESPONSE" | jq -r '.choices[0].message.images[0]' | sed 's|data:image/png;base64,||' | base64 -d > output.png
```

**Cost:** ~$0.067 per image generation (automatically tracked).

## Workflow

### 1. Receive Brief

Get creative brief with:
- Ad concept (price anchor, native, tutorial, etc.)
- Exact copy/text
- Target aspect ratio
- Brand colors (if applicable)
- Reference images (if any)

### 2. Check Brand Guidelines

Read brand info from shared brand documents/wiki first. If structured notes exist, use `brand:*` entries as a quick lookup:
- `brand:name` — company name
- `brand:voice` — tone and style
- `brand:colors` — color palette

### 3. Construct Prompt

Build prompt using template above. Key points:
- Start with aspect ratio
- Be explicit about exact text
- End with exclusions (NO logos, etc.)

### 4. Generate Image

Run API call via OpenRouter, save to output folder:
```
~/documents/{project-slug}/creative/images/{ad-type}-{version}.png
```

### 5. Review Before Sending

**ALWAYS review generated images before sending to user.**

Check for:
- [ ] Text is correct (no garbled words)
- [ ] No hallucinated logos or brand names
- [ ] No unexpected elements
- [ ] Aspect ratio looks correct
- [ ] Overall quality is acceptable

Use the `Read` tool to view the image:
```
Read file_path=/path/to/image.png
```

### 6. Iterate if Needed

If image has issues:
- Simplify the prompt
- Be more explicit about exclusions
- Try regenerating (results vary)

### 7. Deliver

Send via message tool with descriptive caption:
```
message action=send filePath=/path/to/image.png caption="Ad Name (1:1) - Reviewed"
```

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Hallucinated logos | Model fills "empty" space | Add "NO logos. NO brand names." explicitly |
| Garbled text | Too many text instructions | Simplify, use fewer lines |
| Wrong aspect ratio | Not specified clearly | Start prompt with "Generate a square/4:5/etc image" |
| Extra decorations | Over-specified design | Add "no decorations, no borders, no frames" |
| Generic stock look | Vague prompt | Add specific style cues (warm lighting, minimal, etc.) |
| `message.content` is null | Normal for image models | Check `message.images[]` array instead |

## Ad Types

### 1. Native/Organic Creative
- Looks like user content, not an ad
- Notebook, whiteboard, screenshot styles
- Text-heavy, minimal design
- Works great for TOFU

### 2. Price Anchor
- Clean typography on white/simple background
- Comparison format (expensive vs affordable)
- Bold price in accent color
- Works great for MOFU

### 3. Tutorial/Value Bomb
- Instructional design
- Step badges, mockups
- Educational feel
- Works for TOFU (carousel format)

### 4. Testimonial/Social Proof
- Quote format
- Photo or avatar (if provided)
- Company logos (if permitted)
- Works for MOFU/BOFU

### 5. Bold Claim
- Single powerful statement
- Minimal design, maximum impact
- Brand colors
- Works for awareness

## Integration

This skill works with:
- `/campaign_planner` — Provides creative briefs
- `/creative_director` — Orchestrates asset creation
- `/website_brand_analysis` — Provides brand guidelines
- Shared brand docs/wiki plus optional structured `brand:*` notes — brand colors, voice, identity

## Output

Save images to:
```
~/documents/{project-slug}/creative/images/{ad-type}-v{N}.png
```

Examples:
- `{brand}-hero-v1.png`
- `{brand}-price-anchor-v2.png`
- `{brand}-carousel-1-v1.png`
