#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def resolve_path(path_value: str, manifest_dir: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        candidates = [path]
        if str(path).startswith("/documents/"):
            candidates.append(Path("/home/node") / str(path).lstrip("/"))
            candidates.append(Path("/home/growthhacker/.openclaw/workspaces/main/workspace") / str(path).lstrip("/"))
    else:
        candidates = [manifest_dir / path]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError:
        fail("Pillow is required. Install with: python3 -m pip install Pillow")

    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.size
    except Exception as exc:
        fail(f"{path} is not a valid bitmap image: {exc}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("Usage: validate_carousel.py /path/to/carousel-manifest.json")

    manifest_path = Path(sys.argv[1]).expanduser().resolve()
    if not manifest_path.exists():
        fail(f"Manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    images = manifest.get("images")
    if not isinstance(images, list) or not images:
        fail("Manifest must contain a non-empty images array")

    expected_size = None
    for item in images:
        image_id = item.get("id", "<missing id>")
        local_path = item.get("localPath")
        if not local_path:
            fail(f"{image_id}: missing localPath")

        path = resolve_path(local_path, manifest_path.parent)
        if not path.exists():
            fail(f"{image_id}: image file not found: {path}")

        width, height = image_size(path)
        if width != height:
            fail(f"{image_id}: expected 1:1 image, got {width}x{height}")

        declared_width = item.get("actualWidth")
        declared_height = item.get("actualHeight")
        if declared_width is not None and declared_width != width:
            fail(f"{image_id}: actualWidth {declared_width} does not match file width {width}")
        if declared_height is not None and declared_height != height:
            fail(f"{image_id}: actualHeight {declared_height} does not match file height {height}")

        current_size = (width, height)
        if expected_size is None:
            expected_size = current_size
        elif current_size != expected_size:
            fail(f"{image_id}: size {current_size} differs from first image {expected_size}")

    print(f"OK: {len(images)} image(s) validated at {expected_size[0]}x{expected_size[1]}")


if __name__ == "__main__":
    main()
