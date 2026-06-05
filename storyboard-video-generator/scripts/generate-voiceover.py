#!/usr/bin/env python3
"""
generate-voiceover.py — generate voiceover via FAL Gemini 3.1 Flash TTS (warm, emotive).

Default backend is fal-ai/gemini-3.1-flash-tts — supports natural-language style
instructions, inline emotion tags ([sigh], [whispering], [short pause]),
70+ languages including Czech, less robotic than ElevenLabs.

Reads `voiceover` block from `video-brief.json` and produces an MP3 for the
ffmpeg post-mix step.

Usage:
    python3 generate-voiceover.py \\
        --brief /documents/ads/video/[slug]/video-brief.json \\
        --output /documents/ads/video/[slug]/voiceover.mp3

Brief field expected (top-level):
    "voiceover": {
        "backend": "gemini",                         // "gemini" (default) or "elevenlabs"
        "language": "cs",
        "voice": "Aoede",                            // Gemini: Aoede/Callirrhoe/Sulafat/Charon/Kore/...
        "style_instructions": "Speak warmly and quietly, like a trusted friend at quiet morning. Premium calm. Natural Czech accent.",
        "temperature": 0.7,
        "script": "Plný česky text — můžeš použít [short pause], [sigh], [whispering] inline tagy..."
    }
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from runtime_env import ensure_env_var


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--brief", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voice", help="Override the voice from the brief")
    args = parser.parse_args()

    if not ensure_env_var("FAL_KEY"):
        print("❌ FAL_KEY is not set in env, ~/.openclaw/.env, or Control Center secret store")
        sys.exit(1)

    try:
        import fal_client
        import requests
    except ImportError:
        print("❌ fal-client or requests not installed in provider image")
        sys.exit(1)

    brief_path = Path(args.brief)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    brief = json.load(open(brief_path))
    vo = brief.get("voiceover") or {}
    if not vo.get("script"):
        print("❌ Brief.voiceover.script is empty — nothing to synthesize.")
        sys.exit(1)

    backend = vo.get("backend", "gemini").lower()
    text = vo["script"]

    if backend == "gemini":
        voice = args.voice or vo.get("voice", "Aoede")
        style = vo.get("style_instructions", "Speak warmly and quietly, like a trusted friend at quiet morning. Premium calm. Natural emotional delivery.")
        endpoint = "fal-ai/gemini-3.1-flash-tts"

        # Gemini language_code expects descriptive names like "Czech (Czech Republic)"
        # NOT ISO codes. Map common ISO codes → descriptive names.
        LANG_MAP = {
            "cs": "Czech (Czech Republic)",
            "en": "English (US)",
            "en-us": "English (US)",
            "en-gb": "English (UK)",
            "de": "German (Germany)",
            "fr": "French (France)",
            "es": "Spanish (Spain)",
            "it": "Italian (Italy)",
            "pl": "Polish (Poland)",
            "sk": "Slovak (Slovakia)",
        }
        raw_lang = vo.get("language", "cs")
        language_code = LANG_MAP.get(raw_lang.lower(), raw_lang)

        arguments = {
            "prompt": text,
            "voice": voice,
            "style_instructions": style,
            "temperature": float(vo.get("temperature", 0.7)),
            "output_format": "mp3",
        }
        # Only include language_code if explicitly mapped (else let Gemini auto-detect)
        if language_code != raw_lang or raw_lang.lower() in LANG_MAP:
            arguments["language_code"] = language_code
        print(f"→ Endpoint: {endpoint} (Gemini — emotive)")
        print(f"→ Voice: {voice}")
        print(f"→ Style: {style}")
    else:
        # Legacy ElevenLabs fallback
        voice = args.voice or vo.get("voice", "Rachel")
        stability = float(vo.get("stability", 0.5))
        similarity = float(vo.get("similarity_boost", 0.75))
        endpoint = "fal-ai/elevenlabs/tts/multilingual-v2"
        arguments = {
            "text": text,
            "voice": voice,
            "stability": stability,
            "similarity_boost": similarity,
        }
        print(f"→ Endpoint: {endpoint} (ElevenLabs)")
        print(f"→ Voice: {voice}")

    print(f"→ Text length: {len(text)} chars / ~{len(text.split())} words")
    print(f"→ Language: {vo.get('language', 'auto-detected')}")
    print()
    print("--- SCRIPT ---")
    print(text)
    print("--- END SCRIPT ---")
    print()

    start = time.time()
    for attempt in range(3):
        try:
            handler = await fal_client.submit_async(endpoint, arguments=arguments)
            result = await handler.get()
            audio_url = result.get("audio", {}).get("url") if isinstance(result.get("audio"), dict) else result.get("audio_url")
            if not audio_url:
                print(f"   ⚠ no audio.url in response: {result}")
                if attempt == 2:
                    sys.exit(2)
                continue

            resp = requests.get(audio_url, stream=True, timeout=120)
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            elapsed = time.time() - start
            size_kb = output_path.stat().st_size // 1024
            print(f"✅ Done. {output_path.name} ({size_kb} KB, {elapsed:.1f}s)")
            print(f"   path: {output_path}")
            return
        except Exception as e:
            msg = str(e)
            print(f"   ⚠ attempt {attempt + 1}/3 failed: {msg[:200]}")
            if attempt < 2:
                backoff = 15 * (2 ** attempt)
                print(f"   ⏳ backoff {backoff}s")
                await asyncio.sleep(backoff)
            else:
                sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
