#!/usr/bin/env python3
import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Upscale carousel JPEG/PNG files into a 2000px output folder.")
    parser.add_argument("carousel_dir", help="Path to carousel directory")
    parser.add_argument("--to", type=int, default=2000, help="Target square size in pixels")
    args = parser.parse_args()

    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("ERROR: Pillow is required. Install with: python3 -m pip install Pillow")

    source_dir = Path(args.carousel_dir).expanduser().resolve()
    if not source_dir.exists() or not source_dir.is_dir():
        raise SystemExit(f"ERROR: carousel directory not found: {source_dir}")

    output_dir = source_dir / str(args.to)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        path for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    if not files:
        raise SystemExit(f"ERROR: no image files found in {source_dir}")

    resampling = getattr(Image, "Resampling", Image).LANCZOS
    for path in files:
        with Image.open(path) as image:
            image = image.convert("RGB")
            upscaled = image.resize((args.to, args.to), resampling)
            target = output_dir / f"{path.stem}.jpg"
            upscaled.save(target, "JPEG", quality=95, optimize=True)
            print(target)

    print(f"OK: upscaled {len(files)} image(s) to {args.to}x{args.to}")


if __name__ == "__main__":
    main()
