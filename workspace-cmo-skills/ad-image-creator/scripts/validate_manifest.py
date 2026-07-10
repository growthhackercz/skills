#!/usr/bin/env python3
"""Validate ad-image-manifest.json before a publisher step."""

from __future__ import annotations

import argparse
import json
import struct
import sys
from math import gcd
from pathlib import Path
from typing import Any

ASPECT_RATIO_TOLERANCE = 0.015


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValidationError(f"Manifest does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise ValidationError(f"Manifest is not valid JSON: {path}: {error}") from error


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
        return int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1
    if chunk == b"VP8 " and len(data) >= 30:
        return struct.unpack("<H", data[26:28])[0] & 0x3FFF, struct.unpack("<H", data[28:30])[0] & 0x3FFF
    if chunk == b"VP8L" and len(data) >= 25:
        bits = int.from_bytes(data[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    return None


def image_dimensions(path: Path) -> tuple[int, int]:
    if not path.exists() or path.stat().st_size <= 0:
        raise ValidationError(f"Image file does not exist or is empty: {path}")
    data = path.read_bytes()
    dimensions = read_png_dimensions(data) or read_jpeg_dimensions(data) or read_webp_dimensions(data)
    if not dimensions:
        raise ValidationError(f"Unsupported or invalid bitmap image format: {path}")
    return dimensions


def parse_aspect_ratio(value: str) -> float:
    raw = value.strip()
    if ":" in raw:
        left, right = raw.split(":", 1)
        width = float(left)
        height = float(right)
        if width <= 0 or height <= 0:
            raise ValueError
        return width / height
    ratio = float(raw)
    if ratio <= 0:
        raise ValueError
    return ratio


def reduced_aspect_ratio(width: int, height: int) -> str:
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def validate_image(image: dict[str, Any]) -> dict[str, Any]:
    image_id = str(image.get("id") or "")
    local_path = image.get("localPath")
    if not local_path:
        raise ValidationError(f"Image {image_id or '<missing id>'} is missing localPath.")
    path = Path(str(local_path))
    width, height = image_dimensions(path)
    actual_aspect = reduced_aspect_ratio(width, height)
    expected = image.get("expectedAspectRatio") or image.get("aspectRatio")
    status = image.get("status")
    if status != "generated":
        raise ValidationError(f"Image {image_id or path.name} status must be generated, got {status!r}.")
    if image.get("actualWidth") is not None and int(image["actualWidth"]) != width:
        raise ValidationError(f"Image {image_id or path.name} actualWidth mismatch: manifest {image['actualWidth']}, file {width}.")
    if image.get("actualHeight") is not None and int(image["actualHeight"]) != height:
        raise ValidationError(f"Image {image_id or path.name} actualHeight mismatch: manifest {image['actualHeight']}, file {height}.")
    if expected:
        try:
            expected_ratio = parse_aspect_ratio(str(expected))
        except (TypeError, ValueError) as error:
            raise ValidationError(f"Image {image_id or path.name} has invalid expectedAspectRatio: {expected!r}.") from error
        if abs((width / height) - expected_ratio) > ASPECT_RATIO_TOLERANCE:
            raise ValidationError(
                f"Image {image_id or path.name} aspect mismatch: expected {expected}, got {width}x{height} ({actual_aspect})."
            )
    return {
        "id": image_id or path.name,
        "localPath": str(path),
        "actualWidth": width,
        "actualHeight": height,
        "actualAspectRatio": actual_aspect,
        "expectedAspectRatio": expected,
        "status": "ok",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate ad-image-manifest.json bitmap files and aspect ratios.")
    parser.add_argument("manifest", help="Path to ad-image-manifest.json.")
    parser.add_argument("--image-id", action="append", default=[], help="Validate only selected image id. Can be repeated.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    images = manifest.get("images") if isinstance(manifest, dict) else None
    if not isinstance(images, list) or not images:
        raise ValidationError("Manifest must contain a non-empty images array.")
    valid_images = [image for image in images if isinstance(image, dict)]
    selected_ids = set(args.image_id)
    selected = [
        image
        for image in valid_images
        if selected_ids
        and str(image.get("id")) in selected_ids
    ]
    if selected_ids and len(selected) != len(selected_ids):
        found = {str(image.get("id")) for image in selected}
        missing = sorted(selected_ids - found)
        raise ValidationError(f"Manifest is missing image ids: {', '.join(missing)}")
    if not selected_ids:
        selected = [
            image
            for image in valid_images
            if image.get("selectedForPublisher") is True or image.get("status") == "generated"
        ]
    if not selected:
        raise ValidationError("Manifest does not contain any generated/selected image to validate.")
    validated = [validate_image(image) for image in selected]
    print(json.dumps({"ok": True, "manifest": str(manifest_path), "images": validated, "skipped": len(valid_images) - len(selected)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
