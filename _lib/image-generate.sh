#!/bin/bash
# image-generate.sh — unified OpenRouter image generation wrapper
#
# Generates a raster image using any OpenRouter image-capable model and writes it
# to a local file. This keeps one stable image generation contract while letting
# callers switch models (for example Gemini Flash Image vs OpenAI GPT Image 2 on
# OpenRouter).
#
# Usage:
#   image-generate.sh --model MODEL --agent AGENT --prompt "text" --out /documents/file.png
#   image-generate.sh --model MODEL --agent AGENT --body '{"messages":[...]}' --out /documents/file.png
#
# Options:
#   --model         MODEL       OpenRouter model id (required)
#   --agent         AGENT       Agent name for cost attribution (required)
#   --prompt        TEXT        Prompt text (builds a default image-generation body)
#   --body          JSON        Full OpenRouter request body
#   --out           PATH        Output image path (required)
#   --aspect-ratio  RATIO       Optional OpenRouter image_config.aspect_ratio
#   --image-size    SIZE        Optional OpenRouter image_config.image_size
#   --session       SESSION_ID  Session id for tracking (default: "external")
#
# Notes:
#   - Adds `modalities: ["image", "text"]` when building the default body.
#   - Saves the first returned image from `choices[0].message.images[]`.

set -euo pipefail

MODEL=""
AGENT_NAME=""
PROMPT=""
BODY=""
OUT_FILE=""
ASPECT_RATIO=""
IMAGE_SIZE=""
SESSION_ID="external"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --agent) AGENT_NAME="$2"; shift 2 ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    --body) BODY="$2"; shift 2 ;;
    --out) OUT_FILE="$2"; shift 2 ;;
    --aspect-ratio) ASPECT_RATIO="$2"; shift 2 ;;
    --image-size) IMAGE_SIZE="$2"; shift 2 ;;
    --session) SESSION_ID="$2"; shift 2 ;;
    --help|-h)
      sed -n '2,/^$/s/^# \?//p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$MODEL" ]]; then
  echo "Error: --model is required" >&2
  exit 1
fi

if [[ -z "$AGENT_NAME" ]]; then
  echo "Error: --agent is required" >&2
  exit 1
fi

if [[ -z "$OUT_FILE" ]]; then
  echo "Error: --out is required" >&2
  exit 1
fi

if [[ -n "$PROMPT" ]]; then
  BODY=$(
    jq -n \
      --arg prompt "$PROMPT" \
      --arg aspectRatio "$ASPECT_RATIO" \
      --arg imageSize "$IMAGE_SIZE" \
      '
      {
        messages: [
          {
            role: "user",
            content: $prompt
          }
        ],
        modalities: ["image", "text"]
      }
      + (
        if ($aspectRatio != "" or $imageSize != "") then
          {
            image_config:
              ({}
                + (if $aspectRatio != "" then {aspect_ratio: $aspectRatio} else {} end)
                + (if $imageSize != "" then {image_size: $imageSize} else {} end))
          }
        else
          {}
        end
      )
      '
  )
elif [[ -n "$BODY" ]]; then
  BODY=$(printf '%s' "$BODY" | jq '
    . + {
      modalities: (
        if (.modalities | type) == "array" then .modalities else ["image", "text"] end
      )
    }
  ')
elif [[ ! -t 0 ]]; then
  BODY=$(cat | jq '
    . + {
      modalities: (
        if (.modalities | type) == "array" then .modalities else ["image", "text"] end
      )
    }
  ')
else
  echo "Error: provide --prompt, --body, or pipe request JSON to stdin" >&2
  exit 1
fi

RESPONSE=$("$HOME/.openclaw/cs-skills/_lib/openrouter-call.sh" \
  --model "$MODEL" \
  --agent "$AGENT_NAME" \
  --session "$SESSION_ID" \
  --body "$BODY")

printf '%s' "$RESPONSE" \
  | "$HOME/.openclaw/cs-skills/_lib/openrouter-image-extract.sh" --out "$OUT_FILE"
