#!/bin/bash
# openrouter-call.sh — OpenRouter API wrapper with automatic cost tracking
#
# Makes an OpenRouter API call, outputs the full response to stdout,
# and silently reports usage/cost to Mission Control in the background.
#
# Usage:
#   openrouter-call.sh --model MODEL --agent AGENT [--prompt "text"]
#   openrouter-call.sh --model MODEL --agent AGENT --body '{"messages":[...]}'
#   echo '{"messages":[...]}' | openrouter-call.sh --model MODEL --agent AGENT
#
# Options:
#   --model    MODEL       OpenRouter model ID (required)
#   --agent    AGENT       Agent name for cost attribution (required)
#   --prompt   TEXT        Simple text prompt (builds messages array)
#   --body     JSON        Full request body (model field added/overridden)
#   --session  SESSION_ID  Session ID for tracking (default: "external")
#
# Environment:
#   OPENROUTER_API_KEY  OpenRouter API key (required)
#   MC_URL              Mission Control URL (default: http://localhost:3001)
#   MC_API_KEY          MC API key for reporting (falls back to API_KEY)

set -euo pipefail

# Ensure jq is available
export PATH="$HOME/.local/bin:$PATH"

# --- Parse arguments ---
MODEL=""
AGENT_NAME=""
PROMPT=""
BODY=""
SESSION_ID="external"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)   MODEL="$2"; shift 2 ;;
    --agent)   AGENT_NAME="$2"; shift 2 ;;
    --prompt)  PROMPT="$2"; shift 2 ;;
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
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "Error: OPENROUTER_API_KEY not set" >&2
  exit 1
fi

# --- Build request body ---
if [[ -n "$PROMPT" ]]; then
  # Simple text prompt → build messages array
  BODY=$(jq -n --arg model "$MODEL" --arg prompt "$PROMPT" \
    '{model: $model, messages: [{role: "user", content: $prompt}]}')
elif [[ -n "$BODY" ]]; then
  # Full body provided → inject/override model
  BODY=$(echo "$BODY" | jq --arg m "$MODEL" '. + {model: $m}')
elif [[ ! -t 0 ]]; then
  # Read from stdin
  BODY=$(cat | jq --arg m "$MODEL" '. + {model: $m}')
else
  echo "Error: provide --prompt, --body, or pipe request JSON to stdin" >&2
  exit 1
fi

# --- Make the API call ---
RESPONSE=$(curl -s "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
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

  # Extract usage from response
  INPUT_TOKENS=$(echo "$RESPONSE" | jq -r '.usage.prompt_tokens // 0' 2>/dev/null)
  OUTPUT_TOKENS=$(echo "$RESPONSE" | jq -r '.usage.completion_tokens // 0' 2>/dev/null)
  COST=$(echo "$RESPONSE" | jq -r '.usage.cost // 0' 2>/dev/null)

  # Skip if no real usage data
  if [[ "$INPUT_TOKENS" == "0" && "$OUTPUT_TOKENS" == "0" ]]; then exit 0; fi

  # Clean cost (reject negative or null)
  if [[ "$COST" == "null" || "$COST" == "0" ]]; then
    COST_FIELD=""
  else
    # Check if cost is positive
    IS_POSITIVE=$(echo "$COST" | awk '{print ($1 > 0) ? "yes" : "no"}')
    if [[ "$IS_POSITIVE" == "yes" ]]; then
      COST_FIELD="\"cost\": $COST,"
    else
      COST_FIELD=""
    fi
  fi

  curl -s -X POST "$MC_URL/api/tokens" \
    -H "x-api-key: $MC_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"$MODEL\",
      \"sessionId\": \"${AGENT_NAME}:${SESSION_ID}\",
      \"inputTokens\": $INPUT_TOKENS,
      \"outputTokens\": $OUTPUT_TOKENS,
      $COST_FIELD
      \"operation\": \"external_api\"
    }" > /dev/null 2>&1

} &

# Don't wait for background reporting
disown 2>/dev/null || true
