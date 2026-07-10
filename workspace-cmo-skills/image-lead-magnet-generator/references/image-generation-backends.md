# Image Generation Backends — 3 možnosti, volba uživatele v Krok 0.2

Skill podporuje **3 backendy** pro generování obrázků. Volba se děje v **Krok 0.2 SKILL.md** (vyžaduje schválení uživatele) a uloží se do `page-plan.json` (`backend: "openclaw" | "openrouter" | "fal"`).

| Backend | Endpoint / tool | Auth | Kdy zvolit |
|---------|-----------------|------|------------|
| **OpenClaw native** (default) | `image_generate` CLI | žádný (built-in) | Standardní produkční nasazení, billing přes CC |
| **OpenRouter** | `POST openrouter.ai/api/v1/images/generations` | `OPENROUTER_API_KEY` | Vlastní OpenRouter credit, mimo CC billing |
| **FAL.ai** | `POST queue.fal.run/fal-ai/gpt-image-2` | `FAL_KEY` | Dev/test mimo OpenClaw runtime, hi-end print 4096 px |

Všechny 3 backendy používají **GPT Image 2** model, ale liší se v reference image handlingu, billing modelu a dostupnosti.

---

## Backend 1: FAL.ai GPT Image 2.0

### Endpoint

```
fal-ai/gpt-image-2
```

Asynchronous queue (recommended pro batch):
```
POST https://queue.fal.run/fal-ai/gpt-image-2
```

### Authentication

```
Authorization: Key {{FAL_KEY}}
```

`FAL_KEY` je env variable. Skill ji vyžaduje v metadatě:

```yaml
metadata: {"openclaw":{"requires":{"env":["FAL_KEY"]},"primaryEnv":"FAL_KEY"}}
```

### Request body

```json
{
  "prompt": "string — kompletní prompt s style directive + layout + content",
  "image_size": {
    "width": 2480,
    "height": 3508
  },
  "num_images": 1,
  "guidance_scale": 4.5,
  "output_format": "png",
  "negative_prompt": "...",
  "seed": null,
  "reference_images": [
    "data:image/png;base64,...",  // brand-board base64
    "data:image/png;base64,...",  // 08-inspirace base64
    "data:image/png;base64,..."   // optional product photo
  ]
}
```

### Reference images (max 3)

GPT Image 2 přes FAL podporuje **up to 3 reference images** simultaneously. Reference se posílají jako base64 v JSON body.

**Nekódujeme přes URL** — FAL endpoint nemá přístup k Pavlově filesystem. Vždy převést přes Python:

```python
import base64
with open(ref_path, "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")
data_url = f"data:image/png;base64,{encoded}"
```

### Image size limits

GPT Image 2 přes FAL podporuje:
- Min: 256×256
- Max: 4096×4096 (max area)
- Pro A4 portrait 300 DPI: 2480×3508 (8.7M pixels) ✓
- Pro A4 landscape 300 DPI: 3508×2480 ✓
- Pro hi-end print: 4096×3072 nebo 3072×4096

### Cost (k 2026)

- Draft (1240×1754): ~$0.03 / image
- Final (2480×3508): ~$0.10 / image
- Hi-end (4096×3072): ~$0.20 / image

Pro 10-stránkový magnet:
- Draft fáze: 10 × $0.03 = **$0.30**
- Regenerace 30%: 3 × $0.03 = **$0.09**
- Final fáze: 10 × $0.10 = **$1.00**
- **Total ~ $1.40** za jeden magnet

### Response

```json
{
  "images": [
    {
      "url": "https://fal.media/.../result.png",
      "width": 2480,
      "height": 3508,
      "content_type": "image/png"
    }
  ],
  "seed": 12345,
  "request_id": "abc123"
}
```

Stáhni `images[0].url` na lokální disk přes `requests`.

### Async queue workflow

Pro batch generování (10+ obrázků) **doporučujeme async queue** — synchronní endpoint má timeout 60s.

```python
import fal_client

handler = fal_client.submit(
    "fal-ai/gpt-image-2",
    arguments={
        "prompt": prompt,
        "image_size": {"width": 2480, "height": 3508},
        "reference_images": [data_url1, data_url2, data_url3],
    },
)
result = handler.get()  # blokuje až do dokončení (~30-60s)
```

### Rate limits

Default FAL rate limits (free / hobby tier):
- **Concurrent requests:** 4
- **Requests per minute:** 60
- **Requests per day:** depends on plan

V `generate-images.py` použij **semaphore = 4** pro concurrent generation:

```python
import asyncio
sem = asyncio.Semaphore(4)
```

---

## Backend 2: OpenRouter GPT Image 2

### Endpoint

```
POST https://openrouter.ai/api/v1/images/generations
```

### Authentication

```
Authorization: Bearer {{OPENROUTER_API_KEY}}
```

`OPENROUTER_API_KEY` je env variable. Skill ji vyžaduje pokud uživatel zvolí backend `openrouter` v Krok 0.2.

### Request body

```json
{
  "model": "openai/gpt-image-2",
  "prompt": "string — kompletní prompt s style directive + layout + content",
  "size": "2480x3508",
  "n": 1,
  "response_format": "b64_json",
  "quality": "high",
  "image_urls": [
    "data:image/png;base64,...",
    "data:image/png;base64,...",
    "data:image/png;base64,..."
  ]
}
```

### Reference images

OpenRouter routes přes OpenAI image API. Pokud konkrétní routing podporuje image-to-image (image edit), reference images jdou jako `image_urls` (base64 data URIs, max 3). Pokud ne, reference se ignorují a generuje se text-to-image.

### Image size limits

GPT Image 2 přes OpenRouter:
- Min: 256×256
- Max: ~4096 area
- Pro A4 portrait 300 DPI: 2480×3508 ✓
- Pro A4 landscape 300 DPI: 3508×2480 ✓

### Cost (k 2026)

- OpenRouter accepting OpenAI images pricing — ~$0.04 / image (1024px) až ~$0.20 / image (4096px)
- Pro 10-stránkový magnet final fáze: ~$1.00–2.00

### Response

```json
{
  "data": [
    {
      "b64_json": "iVBORw0KGgo..."  // PNG bytes encoded
    }
  ]
}
```

Skript dekóduje `b64_json` přímo do souboru (žádný download URL needed).

### Headers (doporučené)

```
HTTP-Referer: https://cliqsales.com
X-Title: CliqSales image-lead-magnet-generator
```

OpenRouter používá tyto headery pro analytics + billing attribution.

### Pre-check

Před invocation musí být `OPENROUTER_API_KEY` v env. Skript fail-fasts:
```python
if args.backend == "openrouter" and not os.environ.get("OPENROUTER_API_KEY"):
    print("❌ OPENROUTER_API_KEY environment variable required for --backend openrouter")
    sys.exit(1)
```

---

## Backend 3: OpenClaw native `image_generate` (production default)

### Aktuální stav

OpenClaw má native `image_generate` tool jako **doporučený default** — built-in v runtime, žádný API key, billing přes Control Center. Pokud skill běží v OpenClaw runtime kontextu (typický CC deploy), `image_generate` je dostupný a stabilní.

### Použití

```bash
image_generate "{prompt}" \
  --size 2480x3508 \
  --reference /home/node/documents/brand/brand-board.png \
  --reference /home/node/documents/brand/brand-kit/08-inspirace-pro-pdf-materialy.png \
  --output /home/node/documents/lead-magnets/[slug]/_pages/page-01.png
```

### Výhody OpenClaw native vs. FAL

| Aspekt | FAL | OpenClaw native |
|--------|-----|-----------------|
| **Authentication** | API key (FAL_KEY env var) | Built-in (žádné setup) |
| **Cost tracking** | Per-call FAL invoice | Centralizovaný billing |
| **Reference images** | Až 3, base64 v body | Direct file paths via runtime mount |
| **Rate limits** | FAL plan limits | OpenClaw centralized |
| **Latency** | 30-60s per image (queue) | Závisí na backend, obvykle podobné |
| **Reliability** | Stabilní, mature endpoint | Aktuálně beta, doporučuje fallback |
| **Path convention** | Local paths converted to base64 | Runtime path: `/home/node/documents/...` |

### Backend selection v `generate-images.py`

```python
parser.add_argument("--backend", choices=["openclaw", "openrouter", "fal"], default="openclaw",
                    help="Generation backend: openclaw (native, default), openrouter (OPENROUTER_API_KEY), fal (FAL_KEY)")
```

Default = `openclaw`. Volba uživatele v skill Krok 0.2 se uloží do `page-plan.json` pole `backend` a předá se v `--backend $BACKEND` při každém spuštění.

### Path convention pro OpenClaw

OpenClaw runtime má specifickou cestu pro filesystem mount:

| Lokální (Pavel macOS) | Runtime (OpenClaw) |
|------------------------|---------------------|
| `/Users/pavelhrdlicka/Documents/Claude/Projects/[brand]/` | `/home/node/documents/[brand]/` |
| `/documents/brand/brand-board.png` (skill convention) | `/home/node/documents/brand/brand-board.png` |

Když skill předává reference image, **používej runtime cestu** (`/home/node/documents/...`) v `image_generate` voláních. Output ukládej do `/documents/...` (relativní k pracovnímu kontextu skillu).

### Příklad image_generate volání s reference

```bash
# Z OpenClaw runtime kontextu
image_generate "{full prompt}" \
  --size 2480x3508 \
  --reference "/home/node/documents/brand/brand-board.png" \
  --reference "/home/node/documents/brand/brand-kit/08-inspirace-pro-pdf-materialy.png" \
  --output "/home/node/documents/lead-magnets/money-detox/_pages/page-01.png"
```

OpenClaw automaticky převede reference do správného formátu (base64 nebo file upload) podle backend modelu.

---

## Backend selection logika v skill

```python
async def generate_one(page, prompt, refs, output, resolution, backend):
    if backend == "fal":
        return await generate_via_fal(page, prompt, refs, output, resolution)
    elif backend == "openrouter":
        return await generate_via_openrouter(page, prompt, refs, output, resolution)
    elif backend == "openclaw":
        return await generate_via_openclaw(page, prompt, refs, output, resolution)
    else:
        raise ValueError(f"Unknown backend: {backend}")
```

Implementace 3 funkcí v `scripts/generate-images.py`:
- `generate_via_fal` — FAL endpoint `fal-ai/gpt-image-2` (nebo `/edit` s reference), base64 reference v `image_urls`
- `generate_via_openrouter` — `POST openrouter.ai/api/v1/images/generations` s `model: openai/gpt-image-2`, response_format `b64_json`
- `generate_via_openclaw` — subprocess `image_generate` CLI s `--reference` flagem (až 3)

---

## Configuration v `~/.openclaw/openclaw.json`

Skill volbu backendu načítá z `page-plan.json` per magnet (rozhodnutí v Krok 0.2). Pokud chceš nastavit env klíče centrálně přes CC skills config:

```json
{
  "skills": {
    "entries": {
      "image-lead-magnet-generator": {
        "enabled": true,
        "env": {
          "FAL_KEY": "...",                  // pro --backend fal
          "OPENROUTER_API_KEY": "..."        // pro --backend openrouter
        },
        "config": {
          "concurrent_requests": 4,
          "draft_resolution": [1240, 1754],
          "final_resolution": [2480, 3508]
        }
      }
    }
  }
}
```

OpenClaw native (`--backend openclaw`) nevyžaduje žádný klíč. Skill skript fail-fastuje, pokud uživatel zvolí `openrouter` nebo `fal` a odpovídající env variable chybí.

---

## Quality comparison (test fáze)

Při testu obou backendů na stejných promptech porovnej:

1. **Text accuracy** — Czech text s diakritikou (OCR výstup vs. expected)
2. **Brand consistency** — vizuální cohesion napříč 10 stránkami magnetu
3. **Reference adherence** — jak dobře GPT Image 2 reflektuje brand-board mood
4. **Layout quality** — premium designer feel vs. AI-obvious
5. **Cost per magnet** — FAL invoice vs. OpenClaw billing
6. **Speed** — průměrný čas per image
7. **Reliability** — failure rate, retry success rate

Output comparison report se ukládá do `/documents/lead-magnets/[slug]/_backend-comparison.md` pro audit.

---

## Fallback chain

Pokud primární backend selže:

```
1. Try preferred backend (FAL or OpenClaw)
2. Retry 3× with exponential backoff (30s, 60s, 120s)
3. Pokud stále fail → switch na druhý backend
4. Pokud i druhý fail → log error, ask user
```

V `generate-images.py`:

```python
async def generate_with_fallback(page, prompt, refs, output, resolution, primary, secondary):
    try:
        return await generate_one(page, prompt, refs, output, resolution, primary)
    except Exception as e:
        print(f"⚠ Primary backend ({primary}) failed: {e}. Trying {secondary}...")
        return await generate_one(page, prompt, refs, output, resolution, secondary)
```
