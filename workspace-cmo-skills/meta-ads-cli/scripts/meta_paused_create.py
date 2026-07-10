#!/usr/bin/env python3
"""Create a Meta campaign/ad set/creative/ad as PAUSED and save evidence files."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from math import gcd
from pathlib import Path
from typing import Any

DEFAULT_GRAPH_VERSION = "v22.0"
DEFAULT_OPENCLAW_HOME = "/home/node/.openclaw"
SENSITIVE_KEY_PARTS = ("access_token", "token", "secret", "password")
ASPECT_RATIO_TOLERANCE = 0.015


class MetaHelperError(RuntimeError):
    def __init__(self, message: str, detail: Any | None = None):
        super().__init__(message)
        self.detail = detail


def parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def load_env_files(paths: list[Path]) -> dict[str, str]:
    loaded: dict[str, str] = {}
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            parsed = parse_env_line(line)
            if parsed:
                key, value = parsed
                loaded.setdefault(key, value)
    return loaded


def env_value(name: str, env_files: dict[str, str], default: str | None = None) -> str | None:
    return os.environ.get(name) or env_files.get(name) or default


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if any(part in key.lower() for part in SENSITIVE_KEY_PARTS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact(item)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise MetaHelperError(f"JSON file does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise MetaHelperError(f"Invalid JSON file: {path}: {error}") from error


def normalize_account_id(account_id: str) -> str:
    return account_id if account_id.startswith("act_") else f"act_{account_id}"


def parse_aspect_ratio(value: str) -> float:
    raw = value.strip()
    if ":" in raw:
        left, right = raw.split(":", 1)
        try:
            width = float(left)
            height = float(right)
        except ValueError as error:
            raise MetaHelperError(f"Invalid aspect ratio: {value}") from error
        if width <= 0 or height <= 0:
            raise MetaHelperError(f"Invalid aspect ratio: {value}")
        return width / height
    try:
        ratio = float(raw)
    except ValueError as error:
        raise MetaHelperError(f"Invalid aspect ratio: {value}") from error
    if ratio <= 0:
        raise MetaHelperError(f"Invalid aspect ratio: {value}")
    return ratio


def reduced_aspect_ratio(width: int, height: int) -> str:
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def ensure_ratio_matches(width: int, height: int, expected: str) -> None:
    actual_ratio = width / height
    expected_ratio = parse_aspect_ratio(expected)
    if abs(actual_ratio - expected_ratio) > ASPECT_RATIO_TOLERANCE:
        raise MetaHelperError(
            "Image aspect ratio mismatch: "
            f"expected {expected}, got {width}x{height} ({reduced_aspect_ratio(width, height)})."
        )


def read_png_dimensions(data: bytes) -> tuple[int, int] | None:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


def read_jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if data[:2] != b"\xff\xd8":
        return None
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in (0xD8, 0xD9):
            continue
        if index + 2 > len(data):
            break
        segment_length = struct.unpack(">H", data[index : index + 2])[0]
        if segment_length < 2 or index + segment_length > len(data):
            break
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            height = struct.unpack(">H", data[index + 3 : index + 5])[0]
            width = struct.unpack(">H", data[index + 5 : index + 7])[0]
            return width, height
        index += segment_length
    return None


def read_webp_dimensions(data: bytes) -> tuple[int, int] | None:
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = int.from_bytes(data[24:27], "little") + 1
        height = int.from_bytes(data[27:30], "little") + 1
        return width, height
    if chunk == b"VP8 " and len(data) >= 30:
        width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
        return width, height
    if chunk == b"VP8L" and len(data) >= 25:
        bits = int.from_bytes(data[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    return None


def image_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    dimensions = read_png_dimensions(data) or read_jpeg_dimensions(data) or read_webp_dimensions(data)
    if not dimensions:
        raise MetaHelperError(f"Unsupported or invalid bitmap image format: {path}")
    width, height = dimensions
    if width <= 0 or height <= 0:
        raise MetaHelperError(f"Invalid image dimensions for {path}: {width}x{height}")
    return width, height


def manifest_images(manifest: Any) -> list[dict[str, Any]]:
    images = manifest.get("images") if isinstance(manifest, dict) else None
    if not isinstance(images, list):
        raise MetaHelperError("Image manifest must contain an images array.")
    return [image for image in images if isinstance(image, dict)]


def manifest_videos(manifest: Any) -> list[dict[str, Any]]:
    videos = manifest.get("videos") if isinstance(manifest, dict) else None
    if not isinstance(videos, list):
        raise MetaHelperError("Video manifest must contain a videos array.")
    return [video for video in videos if isinstance(video, dict)]


def find_manifest_image(manifest: Any, image_path: Path, image_id: str | None) -> dict[str, Any]:
    images = manifest_images(manifest)
    if image_id:
        matches = [image for image in images if str(image.get("id", "")) == image_id]
        if not matches:
            raise MetaHelperError(f"Image manifest does not contain image id: {image_id}")
        return matches[0]
    resolved = str(image_path)
    basename = image_path.name
    matches = [
        image
        for image in images
        if str(image.get("localPath", "")) == resolved or Path(str(image.get("localPath", ""))).name == basename
    ]
    if len(matches) != 1:
        raise MetaHelperError(
            "Image manifest image is ambiguous; pass --image-id. "
            f"Matched {len(matches)} records for {image_path}."
        )
    return matches[0]


def find_manifest_video(manifest: Any, video_path: Path, video_id: str | None) -> dict[str, Any]:
    videos = manifest_videos(manifest)
    if video_id:
        matches = [video for video in videos if str(video.get("id", "")) == video_id]
        if not matches:
            raise MetaHelperError(f"Video manifest does not contain video id: {video_id}")
        return matches[0]
    resolved = str(video_path)
    basename = video_path.name
    matches = [
        video
        for video in videos
        if str(video.get("localPath", "")) == resolved or Path(str(video.get("localPath", ""))).name == basename
    ]
    if len(matches) != 1:
        raise MetaHelperError(
            "Video manifest video is ambiguous; pass --video-id. "
            f"Matched {len(matches)} records for {video_path}."
        )
    return matches[0]


def validate_image_input(
    image_path: Path,
    image_manifest: Path | None,
    image_id: str | None,
    expected_aspect_ratio: str | None,
) -> dict[str, Any]:
    if not image_path.exists() or image_path.stat().st_size <= 0:
        raise MetaHelperError(f"Image file does not exist or is empty: {image_path}")
    width, height = image_dimensions(image_path)
    result: dict[str, Any] = {
        "image_file": str(image_path),
        "actualWidth": width,
        "actualHeight": height,
        "actualAspectRatio": reduced_aspect_ratio(width, height),
    }
    expected = expected_aspect_ratio
    if image_manifest:
        manifest = load_json(image_manifest)
        image = find_manifest_image(manifest, image_path, image_id)
        result["manifest_file"] = str(image_manifest)
        result["manifest_image_id"] = image.get("id")
        status = image.get("status")
        if status != "generated":
            raise MetaHelperError(f"Image manifest status must be generated, got {status!r}.", image)
        local_path = image.get("localPath")
        if local_path and Path(str(local_path)).name != image_path.name and str(local_path) != str(image_path):
            raise MetaHelperError(f"Image manifest localPath does not match --image-file: {local_path}", image)
        manifest_width = image.get("actualWidth")
        manifest_height = image.get("actualHeight")
        if manifest_width is not None and int(manifest_width) != width:
            raise MetaHelperError(f"Image manifest actualWidth mismatch: manifest {manifest_width}, file {width}.", image)
        if manifest_height is not None and int(manifest_height) != height:
            raise MetaHelperError(f"Image manifest actualHeight mismatch: manifest {manifest_height}, file {height}.", image)
        expected = expected or image.get("expectedAspectRatio") or image.get("aspectRatio")
    if expected:
        ensure_ratio_matches(width, height, str(expected))
        result["expectedAspectRatio"] = str(expected)
    return result


def validate_video_input(video_path: Path, video_manifest: Path | None, video_id: str | None) -> dict[str, Any]:
    if not video_path.exists() or video_path.stat().st_size <= 0:
        raise MetaHelperError(f"Video file does not exist or is empty: {video_path}")
    data = video_path.read_bytes()[:16]
    if not (video_path.name.lower().endswith(".mp4") or data[4:8] == b"ftyp"):
        raise MetaHelperError(f"Video file must be an MP4-compatible file: {video_path}")
    result: dict[str, Any] = {
        "video_file": str(video_path),
        "sizeBytes": video_path.stat().st_size,
    }
    if video_manifest:
        manifest = load_json(video_manifest)
        video = find_manifest_video(manifest, video_path, video_id)
        result["manifest_file"] = str(video_manifest)
        result["manifest_video_id"] = video.get("id")
        status = video.get("status")
        if status != "generated":
            raise MetaHelperError(f"Video manifest status must be generated, got {status!r}.", video)
        local_path = video.get("localPath")
        if local_path and Path(str(local_path)).name != video_path.name and str(local_path) != str(video_path):
            raise MetaHelperError(f"Video manifest localPath does not match --video-file: {local_path}", video)
        if video.get("durationSeconds") is not None:
            result["durationSeconds"] = video.get("durationSeconds")
        if video.get("model") is not None:
            result["model"] = video.get("model")
        if video.get("qualityTier") is not None:
            result["qualityTier"] = video.get("qualityTier")
    return result


def parse_countries(raw: str) -> list[str]:
    countries = [item.strip().upper() for item in raw.split(",") if item.strip()]
    if not countries:
        raise MetaHelperError("At least one country is required.")
    return countries


def assert_no_active(payload: Any, path: str = "$") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            next_path = f"{path}.{key}"
            if key.lower() == "status" and isinstance(value, str) and value.upper() != "PAUSED":
                raise MetaHelperError(f"Unsafe status at {next_path}: {value!r}. Only PAUSED is allowed.")
            assert_no_active(value, next_path)
    elif isinstance(payload, list):
        for idx, value in enumerate(payload):
            assert_no_active(value, f"{path}[{idx}]")
    elif isinstance(payload, str) and payload.upper() == "ACTIVE":
        raise MetaHelperError(f"Unsafe ACTIVE value at {path}.")


def graph_request(
    method: str,
    url: str,
    params: dict[str, Any],
    out_path: Path | None,
    timeout: int,
) -> Any:
    encoded = urllib.parse.urlencode(
        {
            key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
            for key, value in params.items()
            if value is not None
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=encoded if method == "POST" else None, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        if out_path:
            write_json(out_path.with_suffix(".error.json"), detail)
        raise MetaHelperError(f"Meta API {method} failed for {url}: HTTP {error.code}", detail) from error
    if out_path:
        write_json(out_path, data)
    return data


def graph_get(url: str, params: dict[str, Any], out_path: Path, timeout: int) -> Any:
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        write_json(out_path.with_suffix(".error.json"), detail)
        raise MetaHelperError(f"Meta API GET failed for {url}: HTTP {error.code}", detail) from error
    write_json(out_path, data)
    return data


def multipart_upload_image(url: str, access_token: str, image_path: Path, out_path: Path, timeout: int) -> Any:
    if not image_path.exists() or image_path.stat().st_size <= 0:
        raise MetaHelperError(f"Image file does not exist or is empty: {image_path}")

    boundary = f"----cc-meta-{int(time.time() * 1000)}"
    content_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(value.encode("utf-8"))
        parts.append(b"\r\n")

    add_field("access_token", access_token)
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        (
            f'Content-Disposition: form-data; name="filename"; filename="{image_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    parts.append(image_path.read_bytes())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        url,
        data=b"".join(parts),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        write_json(out_path.with_suffix(".error.json"), detail)
        raise MetaHelperError(f"Meta image upload failed: HTTP {error.code}", detail) from error

    write_json(out_path, data)
    return data


def multipart_upload_video(url: str, access_token: str, video_path: Path, out_path: Path, timeout: int) -> Any:
    if not video_path.exists() or video_path.stat().st_size <= 0:
        raise MetaHelperError(f"Video file does not exist or is empty: {video_path}")

    boundary = f"----cc-meta-video-{int(time.time() * 1000)}"
    content_type = mimetypes.guess_type(str(video_path))[0] or "video/mp4"
    parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(value.encode("utf-8"))
        parts.append(b"\r\n")

    add_field("access_token", access_token)
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        (
            f'Content-Disposition: form-data; name="source"; filename="{video_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
    )
    parts.append(video_path.read_bytes())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        url,
        data=b"".join(parts),
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = {"raw": raw}
        write_json(out_path.with_suffix(".error.json"), detail)
        raise MetaHelperError(f"Meta video upload failed: HTTP {error.code}", detail) from error

    write_json(out_path, data)
    return data


def extract_image_hash(upload_response: dict[str, Any], image_path: Path) -> str:
    images = upload_response.get("images")
    if not isinstance(images, dict):
        raise MetaHelperError("Image upload response does not contain images map.", upload_response)
    candidate = images.get(image_path.name) or next(iter(images.values()), None)
    if not isinstance(candidate, dict) or not candidate.get("hash"):
        raise MetaHelperError("Image upload response does not contain image hash.", upload_response)
    return str(candidate["hash"])


def extract_video_id(upload_response: dict[str, Any]) -> str:
    video_id = upload_response.get("id")
    if not video_id:
        raise MetaHelperError("Video upload response does not contain id.", upload_response)
    return str(video_id)


def wait_for_video_ready(
    base_url: str,
    video_id: str,
    access_token: str,
    out_dir: Path,
    timeout_seconds: int,
    request_timeout: int,
) -> Any:
    deadline = time.time() + timeout_seconds
    last_status: Any = None
    attempt = 0
    while True:
        attempt += 1
        status_response = graph_get(
            f"{base_url}/{video_id}",
            {"access_token": access_token, "fields": "id,status"},
            out_dir / "04-video-processing-status.json",
            request_timeout,
        )
        last_status = status_response
        status = status_response.get("status") if isinstance(status_response, dict) else None
        status_text = ""
        if isinstance(status, dict):
            status_text = str(status.get("video_status") or status.get("status") or "").lower()
        elif status is not None:
            status_text = str(status).lower()
        if status_text in {"ready", "available", "published"}:
            return status_response
        if status_text in {"error", "failed"}:
            raise MetaHelperError("Meta video processing failed.", status_response)
        if time.time() >= deadline:
            raise MetaHelperError("Timed out waiting for Meta video processing.", last_status)
        time.sleep(5 if attempt < 6 else 10)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create PAUSED Meta Ads objects and save evidence JSON files.")
    parser.add_argument("--out-dir", required=True, help="Directory for evidence JSON files.")
    parser.add_argument("--image-file", required=True, help="Local JPG/PNG image to upload. For video ads this is the thumbnail image.")
    parser.add_argument("--image-manifest", default=None, help="Optional ad-image-manifest.json to verify before Meta write.")
    parser.add_argument("--image-id", default=None, help="Image id inside --image-manifest. Required when manifest has ambiguous local paths.")
    parser.add_argument("--expected-aspect-ratio", default=None, help="Optional hard aspect-ratio gate, e.g. 1:1, 4:5, 9:16.")
    parser.add_argument("--video-file", default=None, help="Optional local MP4 file. When present, create a video ad creative.")
    parser.add_argument("--video-manifest", default=None, help="Optional ad-video-manifest.json to verify before Meta write.")
    parser.add_argument("--video-id", default=None, help="Video id inside --video-manifest. Required when manifest has ambiguous local paths.")
    parser.add_argument("--video-processing-timeout", type=int, default=180, help="Seconds to wait until uploaded Meta video is ready.")
    parser.add_argument("--campaign-name", required=True)
    parser.add_argument("--adset-name", required=True)
    parser.add_argument("--creative-name", required=True)
    parser.add_argument("--ad-name", required=True)
    parser.add_argument("--landing-url", required=True)
    parser.add_argument("--primary-text", required=True)
    parser.add_argument("--headline", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--cta", default="LEARN_MORE")
    parser.add_argument("--objective", default="OUTCOME_TRAFFIC")
    parser.add_argument("--daily-budget", type=int, required=True, help="Minor units, e.g. 10000 for CZK 100.")
    parser.add_argument("--age-min", type=int, default=18)
    parser.add_argument("--age-max", type=int, default=65)
    parser.add_argument("--countries", default="CZ", help="Comma-separated country codes.")
    parser.add_argument("--dsa-beneficiary", required=True)
    parser.add_argument("--dsa-payor", required=True)
    parser.add_argument("--bid-amount", type=int, default=100)
    parser.add_argument("--graph-version", default=DEFAULT_GRAPH_VERSION)
    parser.add_argument("--account-id", default=None)
    parser.add_argument("--page-id", default=None)
    parser.add_argument("--access-token", default=None)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and write sanitized planned payloads without calling Meta.")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    openclaw_home = Path(os.environ.get("OPENCLAW_HOME", DEFAULT_OPENCLAW_HOME))
    env_files = load_env_files([openclaw_home / ".env"])

    access_token = args.access_token or env_value("META_ACCESS_TOKEN", env_files)
    account_id = args.account_id or env_value("META_AD_ACCOUNT_ID", env_files)
    page_id = args.page_id or env_value("META_PAGE_ID", env_files)
    missing = [name for name, value in {
        "META_ACCESS_TOKEN": access_token,
        "META_AD_ACCOUNT_ID": account_id,
        "META_PAGE_ID": page_id,
    }.items() if not value]
    if missing:
        raise MetaHelperError(f"Missing required Meta config: {', '.join(missing)}")

    out_dir = Path(args.out_dir)
    image_path = Path(args.image_file)
    image_manifest = Path(args.image_manifest) if args.image_manifest else None
    image_validation = validate_image_input(image_path, image_manifest, args.image_id, args.expected_aspect_ratio)
    video_path = Path(args.video_file) if args.video_file else None
    video_manifest = Path(args.video_manifest) if args.video_manifest else None
    video_validation = validate_video_input(video_path, video_manifest, args.video_id) if video_path else None
    write_json(out_dir / "00-image-validation.json", image_validation)
    if video_validation:
        write_json(out_dir / "00-video-validation.json", video_validation)
    if args.daily_budget <= 0:
        raise MetaHelperError("--daily-budget must be greater than zero.")
    if args.age_min < 13 or args.age_max < args.age_min:
        raise MetaHelperError("--age-min/--age-max are invalid.")
    if not args.landing_url.startswith(("http://", "https://")):
        raise MetaHelperError("--landing-url must start with http:// or https://.")

    account = normalize_account_id(str(account_id))
    base = f"https://graph.facebook.com/{args.graph_version}"
    account_url = f"{base}/{account}"

    campaign_payload = {
        "name": args.campaign_name,
        "objective": args.objective,
        "buying_type": "AUCTION",
        "special_ad_categories": [],
        "is_adset_budget_sharing_enabled": "false",
        "status": "PAUSED",
        "access_token": access_token,
    }
    targeting = {
        "age_min": args.age_min,
        "age_max": args.age_max,
        "geo_locations": {
            "countries": parse_countries(args.countries),
            "location_types": ["home", "recent"],
        },
        "targeting_automation": {"advantage_audience": 0},
        "user_age_unknown": False,
    }
    story_spec: dict[str, Any] = {
        "page_id": str(page_id),
        "link_data": {
            "link": args.landing_url,
            "message": args.primary_text,
            "name": args.headline,
            "description": args.description,
            "call_to_action": {
                "type": args.cta,
                "value": {"link": args.landing_url},
            },
        },
    }

    assert_no_active(campaign_payload)
    if args.dry_run:
        planned_story_spec = json.loads(json.dumps(story_spec))
        if video_path:
            planned_story_spec = {
                "page_id": str(page_id),
                "video_data": {
                    "video_id": "[uploaded-video-id]",
                    "image_hash": "[uploaded-thumbnail-image-hash]",
                    "message": args.primary_text,
                    "title": args.headline,
                    "call_to_action": {
                        "type": args.cta,
                        "value": {"link": args.landing_url},
                    },
                },
            }
        else:
            planned_story_spec["link_data"]["image_hash"] = "[uploaded-image-hash]"
        planned_adset_payload = {
            "name": args.adset_name,
            "campaign_id": "[campaign-id]",
            "daily_budget": args.daily_budget,
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LINK_CLICKS",
            "bid_amount": args.bid_amount,
            "destination_type": "WEBSITE",
            "targeting": targeting,
            "dsa_beneficiary": args.dsa_beneficiary,
            "dsa_payor": args.dsa_payor,
            "status": "PAUSED",
            "access_token": access_token,
        }
        planned = {
            "image_validation": image_validation,
            "video_validation": video_validation,
            "campaign": campaign_payload,
            "adset": planned_adset_payload,
            "creative": {
                "name": args.creative_name,
                "object_story_spec": planned_story_spec,
                "access_token": access_token,
            },
            "ad": {
                "name": args.ad_name,
                "adset_id": "[adset-id]",
                "creative": {"creative_id": "[creative-id]"},
                "status": "PAUSED",
                "access_token": access_token,
            },
        }
        assert_no_active(planned)
        write_json(out_dir / "00-dry-run-payloads.json", planned)
        print(json.dumps(redact({"ok": True, "dry_run": True, "out": str(out_dir / "00-dry-run-payloads.json")}), ensure_ascii=False, indent=2))
        return 0

    campaign = graph_request("POST", f"{account_url}/campaigns", campaign_payload, out_dir / "01-create-campaign-response.json", args.timeout)
    campaign_id = campaign.get("id")
    if not campaign_id:
        raise MetaHelperError("Campaign create response does not contain id.", campaign)

    adset_payload = {
        "name": args.adset_name,
        "campaign_id": campaign_id,
        "daily_budget": args.daily_budget,
        "billing_event": "IMPRESSIONS",
        "optimization_goal": "LINK_CLICKS",
        "bid_amount": args.bid_amount,
        "destination_type": "WEBSITE",
        "targeting": targeting,
        "dsa_beneficiary": args.dsa_beneficiary,
        "dsa_payor": args.dsa_payor,
        "status": "PAUSED",
        "access_token": access_token,
    }
    assert_no_active(adset_payload)
    adset = graph_request("POST", f"{account_url}/adsets", adset_payload, out_dir / "02-create-adset-response.json", args.timeout)
    adset_id = adset.get("id")
    if not adset_id:
        raise MetaHelperError("Ad set create response does not contain id.", adset)

    upload = multipart_upload_image(f"{account_url}/adimages", str(access_token), image_path, out_dir / "03-upload-image-response.json", args.timeout)
    image_hash = extract_image_hash(upload, image_path)

    video_id: str | None = None
    if video_path:
        video_upload = multipart_upload_video(
            f"{account_url}/advideos",
            str(access_token),
            video_path,
            out_dir / "04-upload-video-response.json",
            args.timeout,
        )
        video_id = extract_video_id(video_upload)
        wait_for_video_ready(
            base,
            video_id,
            str(access_token),
            out_dir,
            args.video_processing_timeout,
            args.timeout,
        )
        story_spec = {
            "page_id": str(page_id),
            "video_data": {
                "video_id": video_id,
                "image_hash": image_hash,
                "message": args.primary_text,
                "title": args.headline,
                "call_to_action": {
                    "type": args.cta,
                    "value": {"link": args.landing_url},
                },
            },
        }
    else:
        story_spec["link_data"]["image_hash"] = image_hash

    creative_payload = {
        "name": args.creative_name,
        "object_story_spec": story_spec,
        "access_token": access_token,
    }
    creative = graph_request("POST", f"{account_url}/adcreatives", creative_payload, out_dir / "05-create-creative-response.json", args.timeout)
    creative_id = creative.get("id")
    if not creative_id:
        raise MetaHelperError("Creative create response does not contain id.", creative)

    ad_payload = {
        "name": args.ad_name,
        "adset_id": adset_id,
        "creative": {"creative_id": creative_id},
        "status": "PAUSED",
        "access_token": access_token,
    }
    assert_no_active(ad_payload)
    ad = graph_request("POST", f"{account_url}/ads", ad_payload, out_dir / "06-create-ad-response.json", args.timeout)
    ad_id = ad.get("id")
    if not ad_id:
        raise MetaHelperError("Ad create response does not contain id.", ad)

    created_ids = {
        "campaign_id": campaign_id,
        "adset_id": adset_id,
        "creative_id": creative_id,
        "ad_id": ad_id,
        "image_hash": image_hash,
    }
    if video_id:
        created_ids["video_id"] = video_id
    write_json(out_dir / "00-created-ids.json", created_ids)

    verify_params = {"access_token": access_token}
    campaign_verify = graph_get(
        f"{base}/{campaign_id}",
        {**verify_params, "fields": "id,name,status,effective_status,objective,buying_type"},
        out_dir / "07-verify-campaign.json",
        args.timeout,
    )
    adset_verify = graph_get(
        f"{base}/{adset_id}",
        {**verify_params, "fields": "id,name,status,effective_status,daily_budget,billing_event,optimization_goal,targeting,destination_type,campaign_id,dsa_beneficiary,dsa_payor"},
        out_dir / "08-verify-adset.json",
        args.timeout,
    )
    creative_verify = graph_get(
        f"{base}/{creative_id}",
        {**verify_params, "fields": "id,name,object_story_spec"},
        out_dir / "09-verify-creative.json",
        args.timeout,
    )
    ad_verify = graph_get(
        f"{base}/{ad_id}",
        {**verify_params, "fields": "id,name,status,effective_status,adset_id,creative"},
        out_dir / "10-verify-ad.json",
        args.timeout,
    )
    summary = {
        "campaign": campaign_verify,
        "adset": adset_verify,
        "creative": creative_verify,
        "ad": ad_verify,
    }
    write_json(out_dir / "11-verification-summary.json", summary)

    for object_name, data in (("campaign", campaign_verify), ("adset", adset_verify), ("ad", ad_verify)):
        if data.get("status") != "PAUSED":
            raise MetaHelperError(f"Verification failed: {object_name} status is not PAUSED.", data)

    print(json.dumps(created_ids, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MetaHelperError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        if error.detail is not None:
            print(json.dumps(redact(error.detail), ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1)
