#!/bin/bash
# gemini-call.sh — Google Gemini API wrapper with automatic cost tracking
#
# Makes a Gemini generateContent call, outputs the full response to stdout,
# and silently reports usage/cost to Mission Control in the background.
#
# Usage:
#   gemini-call.sh --model MODEL --agent AGENT --body '{"contents":[...]}'
#   echo '{"contents":[...]}' | gemini-call.sh --model MODEL --agent AGENT
#
# Options:
#   --model    MODEL       Gemini model ID (required, e.g. gemini-2.0-flash)
#   --agent    AGENT       Agent name for cost attribution (required)
#   --body     JSON        Request body with contents array
#   --session  SESSION_ID  Session ID for tracking (default: "external")
#
# Environment:
#   GEMINI_API_KEY  Google Gemini API key (required)
#   MC_URL          Mission Control URL (default: http://localhost:3001)
#   MC_API_KEY      MC API key for reporting (falls back to API_KEY)

set -euo pipefail

# Ensure jq is available
export PATH="$HOME/.local/bin:$PATH"

# --- Parse arguments ---
MODEL=""
AGENT_NAME=""
BODY=""
SESSION_ID="external"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)   MODEL="$2"; shift 2 ;;
    --agent)   AGENT_NAME="$2"; shift 2 ;;
    --body)    BODY="$2"; shift 2 ;;
    --session) SESSION_ID="$2"; shift 2 ;;
    --help|-h)
      sed -n '2,/^$/s/^# \?//p' "$0"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# --- Validate ---
if [[ -z "$MODEL" ]]; then
  echo "Error: --model is required" >&2
  exit 1
fi
if [[ -z "$AGENT_NAME" ]]; then
  echo "Error: --agent is required" >&2
  exit 1
fi
if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "Error: GEMINI_API_KEY not set" >&2
  exit 1
fi

# --- Build request body ---
if [[ -n "$BODY" ]]; then
  : # Use as-is
elif [[ ! -t 0 ]]; then
  BODY=$(cat)
else
  echo "Error: provide --body or pipe request JSON to stdin" >&2
  exit 1
fi

# --- Make the API call ---
RESPONSE=$(curl -s -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$BODY")

# Output full response for the agent
echo "$RESPONSE"

# --- Report cost to Mission Control (background, best-effort) ---
{
  MC_URL="${MC_URL:-http://localhost:3001}"
  MC_KEY="${MC_API_KEY:-${API_KEY:-}}"

  # Skip if no MC API key
  if [[ -z "$MC_KEY" ]]; then exit 0; fi

  # Gemini returns usageMetadata.promptTokenCount / candidatesTokenCount
  INPUT_TOKENS=$(echo "$RESPONSE" | jq -r '.usageMetadata.promptTokenCount // 0' 2>/dev/null)
  OUTPUT_TOKENS=$(echo "$RESPONSE" | jq -r '.usageMetadata.candidatesTokenCount // 0' 2>/dev/null)

  # Skip if no real usage data
  if [[ "$INPUT_TOKENS" == "0" && "$OUTPUT_TOKENS" == "0" ]]; then exit 0; fi

  # Model name for MC (prefix with google/ for pricing lookup)
  MC_MODEL="google/${MODEL}"

  curl -s -X POST "$MC_URL/api/tokens" \
    -H "x-api-key: $MC_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$MC_MODEL\",
      \"sessionId\": \"${AGENT_NAME}:${SESSION_ID}\",
      \"inputTokens\": $INPUT_TOKENS,
      \"outputTokens\": $OUTPUT_TOKENS,
      \"operation\": \"external_api\"
    }" > /dev/null 2>&1

} &

# Don't wait for background reporting
disown 2>/dev/null || true
