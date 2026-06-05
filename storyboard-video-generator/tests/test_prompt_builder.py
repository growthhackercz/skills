#!/usr/bin/env python3
"""Smoke tests for build_combined_prompt() — no FAL calls.

Run:
    python3 tests/test_prompt_builder.py

Verifies:
- Prompt assembles cleanly for representative briefs
- PRODUCT COUNT clause appears when product refs present
- CHARACTER COUNT clause appears
- Multi-location vs scene_continuity branches behave
- Voiceover headroom clause toggles correctly
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path

# Allow `python3 tests/test_prompt_builder.py` from any cwd
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "scripts"))

# Import target — script filename has hyphens, so use importlib.
import importlib.util
spec = importlib.util.spec_from_file_location(
    "generate_video_singleshot",
    ROOT / "scripts" / "generate-video-singleshot.py",
)
gvs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gvs)

import runtime_env


FIXTURES = ROOT / "tests" / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def assert_in(needle: str, haystack: str, label: str):
    assert needle in haystack, f"❌ {label}: expected substring not found:\n   {needle!r}"
    print(f"   ✓ {label}")


def assert_not_in(needle: str, haystack: str, label: str):
    assert needle not in haystack, f"❌ {label}: unexpected substring present:\n   {needle!r}"
    print(f"   ✓ {label}")


def test_product_with_storyboard_and_refs():
    print("== single-location product, storyboard + 5 product refs, with voiceover ==")
    brief = load("single-location-product.json")
    prompt = gvs.build_combined_prompt(
        brief, ref_count=6, has_storyboard_first=True, has_voiceover=True,
    )
    # Single-instance product clause must be present (the duplication-fix)
    assert_in("exactly ONE product instance per shot", prompt, "PRODUCT single-instance clause")
    assert_in("never duplicated, mirrored, echoed", prompt, "no-duplication wording")
    assert_in("@Image2-@Image6", prompt, "product tag range")
    assert_in("angle/lighting variants of that SAME single physical object", prompt, "same-object reference framing")
    # Character clause still in
    assert_in("never duplicated, mirrored, or echoed within a frame", prompt, "CHARACTER COUNT clause")
    # Voiceover clause toggled on
    assert_in("pre-rendered voiceover is mixed on top in post", prompt, "VO headroom clause")
    assert_not_in("NO dialog, NO sung lyrics", prompt, "no-VO clause correctly omitted")
    # Brand archetype dynamic
    assert_in("Czech woman late 40s", prompt, "character description injected")


def test_no_product_no_voiceover():
    print("== multi-location, no product, no voiceover ==")
    brief = load("multi-location-no-vo.json")
    prompt = gvs.build_combined_prompt(
        brief, ref_count=1, has_storyboard_first=True, has_voiceover=False,
    )
    # Storyboard-only — no product clause
    assert_not_in("exactly ONE product instance", prompt, "no PRODUCT clause when storyboard-only")
    # Music-only audio clause
    assert_in("NO dialog, NO sung lyrics", prompt, "no-VO audio clause")
    assert_not_in("pre-rendered voiceover", prompt, "VO clause correctly omitted")


def test_storyboard_only_with_product_brief():
    print("== single-location product brief, but ref_count=1 (storyboard only) ==")
    brief = load("single-location-product.json")
    prompt = gvs.build_combined_prompt(
        brief, ref_count=1, has_storyboard_first=True, has_voiceover=True,
    )
    # When ref_count=1, only @Image1 is referenced — no product fidelity clause
    assert_not_in("@Image2", prompt, "no @Image2 tag when ref_count=1")
    assert_not_in("exactly ONE product instance", prompt, "no PRODUCT clause when no product refs")


def test_collect_references_storyboard_first_product_second():
    print("== collect_references maps storyboard to @Image1 and product to @Image2 ==")
    brief = load("single-location-product.json")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        storyboard = work / "01-master-storyboard.png"
        hero = work / "hero.jpg"
        storyboard.write_bytes(b"storyboard")
        hero.write_bytes(b"hero")
        brief["product"]["hero_image"] = str(hero)
        brief["product"]["additional_images"] = []

        refs = gvs.collect_references(
            brief,
            work / "video-brief.json",
            max_refs=6,
            include_storyboard=True,
        )
        assert refs == [storyboard, hero], f"❌ unexpected refs order: {[p.name for p in refs]}"
        print("   ✓ reference order")

        prompt = gvs.build_combined_prompt(
            brief,
            ref_count=len(refs),
            has_storyboard_first=bool(refs and refs[0] == storyboard),
            has_voiceover=True,
        )
        assert_in("@Image1 — master storyboard", prompt, "storyboard legend")
        assert_in("@Image2 — angle variants of the SAME single physical product", prompt, "single product ref legend")
        assert_not_in("@Image3", prompt, "no dangling product ref")


def test_fal_key_resolves_from_control_center_secret_store():
    print("== runtime env resolves FAL_KEY from Control Center secret store ==")
    previous_home = os.environ.get("OPENCLAW_HOME")
    previous_fal = os.environ.pop("FAL_KEY", None)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "control-center-secrets.json").write_text(
                json.dumps({"FAL_KEY": "test-secret-key"}),
                encoding="utf-8",
            )
            os.environ["OPENCLAW_HOME"] = str(root)

            value = runtime_env.ensure_env_var("FAL_KEY")
            assert value == "test-secret-key", f"❌ unexpected FAL_KEY resolution: {value!r}"
            assert os.environ.get("FAL_KEY") == "test-secret-key", "❌ FAL_KEY not exported into process env"
            print("   ✓ secret store fallback")
    finally:
        if previous_home is None:
            os.environ.pop("OPENCLAW_HOME", None)
        else:
            os.environ["OPENCLAW_HOME"] = previous_home
        if previous_fal is None:
            os.environ.pop("FAL_KEY", None)
        else:
            os.environ["FAL_KEY"] = previous_fal


def main():
    tests = [
        test_product_with_storyboard_and_refs,
        test_no_product_no_voiceover,
        test_storyboard_only_with_product_brief,
        test_collect_references_storyboard_first_product_second,
        test_fal_key_resolves_from_control_center_secret_store,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print()
        except AssertionError as e:
            print(e)
            print()
            failed += 1
    if failed:
        print(f"❌ {failed}/{len(tests)} test(s) failed")
        sys.exit(1)
    print(f"✅ All {len(tests)} test(s) passed")


if __name__ == "__main__":
    main()
