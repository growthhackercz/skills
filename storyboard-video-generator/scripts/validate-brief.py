#!/usr/bin/env python3
"""
validate-brief.py — validate `video-brief.json` against schema + Seedance constraints.

Exits 0 if valid, 1 if errors found. Warnings print to stderr but don't fail.
"""
import argparse
import json
import sys
from pathlib import Path


def validate(brief: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    required_top = ["campaign_slug", "version", "platform", "aspect_ratio", "duration_total_s", "tier", "cuts"]
    for field in required_top:
        if field not in brief:
            errors.append(f"missing required top-level field: {field}")

    aspect = brief.get("aspect_ratio")
    if aspect not in ("9:16", "1:1", "16:9"):
        errors.append(f"aspect_ratio must be one of 9:16, 1:1, 16:9 (got: {aspect})")

    tier = brief.get("tier")
    if tier not in ("standard", "fast"):
        errors.append(f"tier must be 'standard' or 'fast' (got: {tier})")

    cuts = brief.get("cuts", [])
    if not cuts:
        errors.append("cuts array is empty")

    cut_total = 0
    for i, cut in enumerate(cuts):
        cut_id = cut.get("id", f"cut-{i+1:02d}")

        for field in ["id", "duration", "shot_type", "video_prompt"]:
            if field not in cut:
                errors.append(f"{cut_id}: missing field '{field}'")

        duration = cut.get("duration")
        if isinstance(duration, str):
            try:
                duration = int(duration)
            except ValueError:
                errors.append(f"{cut_id}: duration must be int (got: {duration!r})")
                continue

        if duration is not None:
            if duration < 3:
                errors.append(f"{cut_id}: duration {duration}s < 3s (storyboard panels need >= 3s)")
            elif duration > 15:
                errors.append(f"{cut_id}: duration {duration}s > Seedance max 15s")
            cut_total += duration

    declared_total = brief.get("duration_total_s")
    if declared_total and cuts:
        if abs(cut_total - declared_total) > 2:
            errors.append(f"cut durations sum to {cut_total}s but duration_total_s is {declared_total}s")

    if declared_total and declared_total > 15:
        errors.append(f"duration_total_s {declared_total}s > Seedance single-call max 15s")

    # cut_count == 5 is the layout-friendly default. Any deviation breaks the
    # 3×2 grid (16:9 / 1:1) or 6×1 strip (9:16) — surface this as an error so
    # users know the storyboard layout will be ugly.
    sc = brief.get("shared_choices", {})
    cut_count = sc.get("cut_count", len(cuts))
    if cut_count != 5:
        errors.append(
            f"shared_choices.cut_count={cut_count} — only 5 is supported by the current "
            f"storyboard layout (3×2 grid / 6×1 strip = 5 cuts + 1 NOTES cell)"
        )

    audio = brief.get("audio", {})
    preset = audio.get("preset", "ambient-music")
    valid_presets = {"silent", "ambient-music"}
    if preset not in valid_presets:
        errors.append(f"audio.preset invalid: {preset} (valid: {', '.join(sorted(valid_presets))})")

    # Product references
    product = brief.get("product")
    if product:
        hero = product.get("hero_image")
        if hero and not Path(hero).exists():
            warnings.append(f"product.hero_image path doesn't exist locally: {hero}")
        if not brief.get("product_visual_identity"):
            warnings.append(
                "product is set but product_visual_identity is missing — high risk of "
                "product hallucination in storyboard frames"
            )

    # Character description
    char = brief.get("character") or {}
    if not char.get("description"):
        warnings.append(
            "character.description missing — Seedance prompt falls back to generic archetype"
        )

    # Voiceover sanity
    vo = brief.get("voiceover")
    if vo:
        if not vo.get("script"):
            errors.append("voiceover block present but script is empty")
        else:
            words = len(vo["script"].split())
            # ~3 words/s for warm Czech narration. 13s ceiling = ~39 words.
            if words > 45:
                warnings.append(
                    f"voiceover.script is {words} words (~{words / 3:.1f}s) — recommended "
                    f"max 45 words / 13s for a 15s ad. Risk of overlap with outro music."
                )

    return errors, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"❌ File not found: {path}")
        sys.exit(1)

    try:
        with open(path, "r", encoding="utf-8") as f:
            brief = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    errors, warnings = validate(brief)

    for w in warnings:
        print(f"⚠️  {w}", file=sys.stderr)

    if errors:
        print(f"❌ {len(errors)} validation error(s):")
        for e in errors:
            print(f"   • {e}")
        sys.exit(1)

    cuts = brief.get("cuts", [])
    total_sec = sum(int(c.get("duration", 0)) for c in cuts)
    price_per_sec = 0.3024 if brief.get("tier") == "standard" else 0.2419
    estimated_cost = total_sec * price_per_sec

    print(f"✅ Brief valid: {brief['campaign_slug']}")
    print(f"   Platform: {brief.get('platform')}")
    print(f"   Aspect: {brief.get('aspect_ratio')}")
    print(f"   Tier: {brief.get('tier')}")
    print(f"   Cuts: {len(cuts)} × avg {total_sec / max(len(cuts), 1):.1f}s = {total_sec}s")
    print(f"   Estimated cost: ${estimated_cost:.2f}")
    if warnings:
        print(f"   ({len(warnings)} warning(s) above)")


if __name__ == "__main__":
    main()
