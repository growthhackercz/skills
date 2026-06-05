#!/bin/bash
# openrouter-image-extract.sh — extract an image from an OpenRouter response
#
# Usage:
#   openrouter-image-extract.sh --out /documents/path/image.png < response.json
#   openrouter-image-extract.sh --out /documents/path/image.png --response "$RESPONSE"
#
# Supports OpenRouter image response variants:
# - choices[0].message.images[0] as a data URI string
# - choices[0].message.images[0].image_url.url as a data URI string
# - choices[0].message.images[0].url or .data fallback

set -euo pipefail

OUT_FILE=""
RESPONSE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) OUT_FILE="$2"; shift 2 ;;
    --response) RESPONSE="$2"; shift 2 ;;
    --help|-h)
      sed -n '2,/^$/s/^# \?//p' "$0"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$OUT_FILE" ]]; then
  echo "IMAGE_GENERATION_FAILED: --out is required" >&2
  exit 1
fi

if [[ -z "$RESPONSE" ]]; then
  RESPONSE="$(cat)"
fi

if [[ -z "$RESPONSE" ]]; then
  echo "IMAGE_GENERATION_FAILED: empty OpenRouter response" >&2
  exit 1
fi

IMAGE_DATA=$(printf '%s' "$RESPONSE" | jq -r '
  .choices[0].message.images[0] // empty
  | if type == "string" then .
    elif type == "object" then (.image_url.url // .url // .data // empty)
    else empty
    end
')

if [[ -z "$IMAGE_DATA" || "$IMAGE_DATA" == "null" ]]; then
  echo "IMAGE_GENERATION_FAILED: no image returned" >&2
  printf '%s\n' "$RESPONSE" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUT_FILE")"
TMP_FILE="$(mktemp "${OUT_FILE}.tmp.XXXXXX")"

if ! printf '%s' "$IMAGE_DATA" \
  | sed -E 's|^data:image/[^;]+;base64,||' \
  | tr -d '\r\n' \
  | base64 -d > "$TMP_FILE"; then
  rm -f "$TMP_FILE"
  echo "IMAGE_GENERATION_FAILED: invalid base64 image data" >&2
  printf '%s\n' "$RESPONSE" >&2
  exit 1
fi

if ! test -s "$TMP_FILE"; then
  rm -f "$TMP_FILE"
  echo "IMAGE_GENERATION_FAILED: decoded image is empty" >&2
  printf '%s\n' "$RESPONSE" >&2
  exit 1
fi

mv "$TMP_FILE" "$OUT_FILE"
file "$OUT_FILE"
echo "IMAGE_GENERATED: $OUT_FILE"
