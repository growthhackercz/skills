#!/usr/bin/env python3
"""Generate ad videos through the Control Center fal.ai video endpoint."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_ENV_FILES = (
    "/home/node/.openclaw/secrets/cliqsales.env",
    "/home/node/.openclaw/secrets/ghl.env",
    "/home/node/.openclaw/.env",
)
ALLOWED_MODES = {"text-to-video", "image-to-video"}
ALLOWED_DURATIONS = {str(value) for value in range(3, 16)}
ALLOWED_ASPECT_RATIOS = {"16:9", "9:16", "1:1"}
ALLOWED_QUALITY_TIERS = {"standard", "pro", "4k"}
ALLOWED_SHOT_TYPES = {"customize", "intelligent"}


class AdVideoError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, detail: Any | None = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


def parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def load_env_file(path: str | None) -> None:
    candidates = [path] if path else list(DEFAULT_ENV_FILES)
    for candidate in candidates:
        if not candidate:
            continue
        env_path = Path(candidate)
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            parsed = parse_env_line(line)
            if parsed:
                os.environ.setdefault(parsed[0], parsed[1])
        return


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise AdVideoError(f"Missing required environment variable: {name}")
    return value


def read_json_file(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise AdVideoError(f"JSON file does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise AdVideoError(f"Invalid JSON file {path}: {error}") from error
    if not isinstance(data, dict):
        raise AdVideoError(f"Expected JSON object in {path}")
    return data


def json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def first_bool(*values: Any) -> bool:
    for value in values:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off"}:
                return False
    return False


def default_duration_for_item(item: dict[str, Any]) -> str:
    platform = (first_string(item.get("platform")) or "").lower()
    fmt = (first_string(item.get("format")) or "").lower()
    objective = (first_string(item.get("objective")) or "").lower()

    if "linkedin" in platform:
        return "15"
    if "google" in platform or "pmax" in fmt or "youtube" in fmt:
        return "15"
    if "story" in fmt or "reel" in fmt or "short" in fmt:
        return "10"
    if "awareness" in objective or "explainer" in fmt or "demo" in fmt:
        return "15"
    if "meta" in platform or "facebook" in platform or "instagram" in platform:
        return "10"
    return "10"


def normalize_multi_prompt(value: Any, item_id: str) -> list[dict[str, str]] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise AdVideoError(f"{item_id}: multiPrompt/multi_prompt must be a non-empty list")
    normalized: list[dict[str, str]] = []
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            raise AdVideoError(f"{item_id}: multiPrompt item {index} must be an object")
        prompt = first_string(entry.get("prompt"))
        if not prompt:
            raise AdVideoError(f"{item_id}: multiPrompt item {index} requires prompt")
        duration = first_string(entry.get("duration"))
        segment: dict[str, str] = {"prompt": prompt}
        if duration:
            if duration not in ALLOWED_DURATIONS:
                raise AdVideoError(f"{item_id}: invalid multiPrompt duration {duration}; use 3-15")
            segment["duration"] = duration
        normalized.append(segment)
    return normalized


def multi_prompt_total_duration(multi_prompt: list[dict[str, str]] | None) -> str | None:
    if not multi_prompt or not all("duration" in item for item in multi_prompt):
        return None
    total = sum(int(item["duration"]) for item in multi_prompt)
    if 3 <= total <= 15:
        return str(total)
    return None


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "video"


def video_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    videos = data.get("videos")
    if isinstance(videos, list):
        items = [item for item in videos if isinstance(item, dict)]
    elif "mode" in data:
        items = [data]
    else:
        raise AdVideoError("Input must include videos[] or a single video object")
    if not items:
        raise AdVideoError("No video items found")
    return items


def validate_video_item(item: dict[str, Any], index: int) -> dict[str, Any]:
    item_id = first_string(item.get("id")) or f"video-{index:03d}"
    mode = first_string(item.get("mode")) or "text-to-video"
    if mode not in ALLOWED_MODES:
        raise AdVideoError(f"{item_id}: invalid mode {mode}")

    prompt = first_string(item.get("prompt"))
    multi_prompt = normalize_multi_prompt(item.get("multiPrompt", item.get("multi_prompt")), item_id)
    image_url = first_string(item.get("imageUrl"), item.get("image_url"))
    if mode == "text-to-video" and not prompt and not multi_prompt:
        raise AdVideoError(f"{item_id}: text-to-video requires prompt or multiPrompt")
    if prompt and multi_prompt:
        raise AdVideoError(f"{item_id}: use prompt or multiPrompt, not both")
    if mode == "image-to-video" and not image_url:
        raise AdVideoError(f"{item_id}: image-to-video requires imageUrl")

    duration = first_string(item.get("duration")) or multi_prompt_total_duration(multi_prompt) or default_duration_for_item(item)
    if duration not in ALLOWED_DURATIONS:
        raise AdVideoError(f"{item_id}: invalid duration {duration}; use 3-15")

    aspect_ratio = first_string(item.get("aspectRatio"), item.get("aspect_ratio")) or "16:9"
    if aspect_ratio not in ALLOWED_ASPECT_RATIOS:
        raise AdVideoError(f"{item_id}: invalid aspectRatio {aspect_ratio}")

    quality_tier = (first_string(item.get("qualityTier"), item.get("quality_tier")) or "pro").lower()
    if quality_tier == "premium":
        quality_tier = "pro"
    if quality_tier not in ALLOWED_QUALITY_TIERS:
        raise AdVideoError(f"{item_id}: invalid qualityTier {quality_tier}; use standard, pro or 4k")

    shot_type = (first_string(item.get("shotType"), item.get("shot_type")) or "customize").lower()
    if shot_type not in ALLOWED_SHOT_TYPES:
        raise AdVideoError(f"{item_id}: invalid shotType {shot_type}; use customize or intelligent")

    filename = first_string(item.get("filename")) or f"{slugify(item_id)}.mp4"
    if not filename.lower().endswith(".mp4"):
        filename = f"{filename}.mp4"

    request: dict[str, Any] = {
        "mode": mode,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "quality_tier": quality_tier,
        "generate_audio": first_bool(item.get("generateAudio"), item.get("generate_audio")),
        "save_to_disk": False,
    }
    if multi_prompt:
        request["multi_prompt"] = multi_prompt
        request["shot_type"] = shot_type
    elif prompt:
        request["prompt"] = prompt
    if image_url:
        request["image_url"] = image_url
    negative = first_string(item.get("negativePrompt"), item.get("negative_prompt"))
    if negative:
        request["negative_prompt"] = negative
    cfg_scale = item.get("cfgScale", item.get("cfg_scale"))
    if isinstance(cfg_scale, (int, float)):
        request["cfg_scale"] = cfg_scale
    end_image = first_string(item.get("endImageUrl"), item.get("end_image_url"))
    if end_image:
        request["end_image_url"] = end_image

    return {
        "id": item_id,
        "platform": first_string(item.get("platform")) or "unspecified",
        "format": first_string(item.get("format")) or "video",
        "filename": filename,
        "request": request,
        "sourceAdId": first_string(item.get("sourceAdId"), item.get("source_ad_id")),
        "duration": duration,
        "qualityTier": quality_tier,
    }


def validate_input(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [validate_video_item(item, index) for index, item in enumerate(video_items(data), start=1)]


def default_output_dir(input_path: str) -> Path:
    parent = Path(input_path).resolve().parent
    if parent.name == "videos":
        return parent
    return parent / "videos"


class ControlCenterVideoClient:
    def __init__(self) -> None:
        self.base_url = require_env("CC_URL").rstrip("/")
        self.api_key = require_env("CC_API_KEY")

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self.base_url}/api/media/video",
            data=json_dumps(payload),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-api-key": self.api_key,
                "User-Agent": "ControlCenterAdVideoCreator/1.0",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=900) as response:
                raw = response.read().decode("utf-8", errors="replace")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            detail_text = error.read().decode("utf-8", errors="replace")
            try:
                detail_obj = json.loads(detail_text) if detail_text else {}
            except json.JSONDecodeError:
                detail_obj = detail_text
            raise AdVideoError(f"Control Center video API returned HTTP {error.code}: {detail_text[:1000]}", error.code, detail_obj)
        except urllib.error.URLError as error:
            raise AdVideoError(f"Control Center video request failed: {error.reason}")


def download_file(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=300) as response:
            content_type = response.headers.get("Content-Type") or mimetypes.guess_type(str(output_path))[0]
            data = response.read()
    except urllib.error.URLError as error:
        raise AdVideoError(f"Video download failed: {error.reason}") from error
    if not data:
        raise AdVideoError(f"Downloaded video is empty: {url}")
    if content_type and "video" not in content_type and "octet-stream" not in content_type:
        raise AdVideoError(f"Downloaded URL does not look like video ({content_type}): {url}")
    output_path.write_bytes(data)


def write_manifest(output_dir: Path, data: dict[str, Any], results: list[dict[str, Any]]) -> Path:
    manifest = {
        "campaignSlug": first_string(data.get("campaignSlug")) or output_dir.parent.name,
        "generator": "fal.ai:control-center-video-api",
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "videos": results,
    }
    path = output_dir.parent / "ad-video-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def build_generate_result(
    mode: str,
    total: int,
    results: list[dict[str, Any]],
    failed: int,
    manifest_path: Path | None,
    in_progress: bool,
) -> dict[str, Any]:
    return {
        "ok": failed == 0 and not in_progress,
        "inProgress": in_progress,
        "mode": mode,
        "total": total,
        "generated": len([item for item in results if item.get("status") == "generated"]),
        "failed": failed,
        "manifestPath": str(manifest_path) if manifest_path else None,
        "results": results,
    }


def write_result_file(path: str | None, data: dict[str, Any]) -> None:
    if not path:
        return
    result_path = Path(path)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command_validate(args: argparse.Namespace) -> int:
    data = read_json_file(args.input)
    videos = validate_input(data)
    print(json.dumps({"ok": True, "video_count": len(videos), "videos": videos}, ensure_ascii=False, indent=2))
    return 0


def command_generate(args: argparse.Namespace) -> int:
    data = read_json_file(args.input)
    videos = validate_input(data)
    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir(args.input)
    if args.dry_run:
        print(json.dumps({"ok": True, "dryRun": True, "outputDir": str(output_dir), "videos": videos}, ensure_ascii=False, indent=2))
        return 0

    mode = args.mode.strip().lower()
    client = ControlCenterVideoClient()
    results: list[dict[str, Any]] = []
    failed = 0
    manifest_path: Path | None = None
    for video in videos:
        output_path = output_dir / video["filename"]
        try:
            print(
                f"Generating {video['id']} platform={video['platform']} "
                f"duration={video['duration']} quality={video['qualityTier']}",
                file=sys.stderr,
                flush=True,
            )
            response = client.generate(video["request"])
            video_url = first_string(response.get("video_url"), response.get("url"))
            if not video_url:
                raise AdVideoError(f"{video['id']}: video API response did not include video_url", detail=response)
            download_file(video_url, output_path)
            results.append({
                "id": video["id"],
                "platform": video["platform"],
                "format": video["format"],
                "localPath": str(output_path),
                "videoUrl": video_url,
                "requestId": first_string(response.get("request_id")),
                "durationSeconds": response.get("duration_seconds"),
                "qualityTier": response.get("quality_tier") or video.get("qualityTier"),
                "model": response.get("model"),
                "estimatedCost": response.get("estimated_cost"),
                "sourceAdId": video.get("sourceAdId"),
                "status": "generated",
            })
            print(f"Generated {video['id']} -> {output_path}", file=sys.stderr, flush=True)
        except Exception as error:  # noqa: BLE001
            failed += 1
            result: dict[str, Any] = {
                "id": video["id"],
                "platform": video["platform"],
                "format": video["format"],
                "status": "failed",
                "error": str(error),
            }
            if isinstance(error, AdVideoError):
                result["httpStatus"] = error.status
                result["detail"] = error.detail
            results.append(result)
            if mode == "strict":
                manifest_path = write_manifest(output_dir, data, results)
                write_result_file(
                    args.result_file,
                    build_generate_result(mode, len(videos), results, failed, manifest_path, in_progress=False),
                )
                break
        manifest_path = write_manifest(output_dir, data, results)
        write_result_file(
            args.result_file,
            build_generate_result(mode, len(videos), results, failed, manifest_path, in_progress=len(results) < len(videos)),
        )

    if manifest_path is None:
        manifest_path = write_manifest(output_dir, data, results)
    final_result = build_generate_result(mode, len(videos), results, failed, manifest_path, in_progress=False)
    write_result_file(args.result_file, final_result)
    print(json.dumps(final_result, ensure_ascii=False, indent=2))
    return 0 if failed == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate ad videos through Control Center fal.ai video API")
    parser.add_argument("--env-file", help="Optional env file path.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--input", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--input", required=True)
    generate.add_argument("--output-dir")
    generate.add_argument("--mode", choices=["continue", "strict"], default="continue")
    generate.add_argument("--result-file", help="Write progress and final JSON to this file while long videos run.")
    generate.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    load_env_file(args.env_file)
    try:
        if args.command == "validate":
            return command_validate(args)
        if args.command == "generate":
            return command_generate(args)
        raise AdVideoError(f"Unknown command: {args.command}")
    except AdVideoError as error:
        print(json.dumps({
            "ok": False,
            "error": str(error),
            "status": error.status,
            "detail": error.detail,
        }, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
