"""Resize/select images while preserving their aspect ratio."""
import argparse
from pathlib import Path
from PIL import Image, ImageOps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-s", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1500)
    parser.add_argument("--height", type=int)
    parser.add_argument("--skip", type=int, default=1)
    args = parser.parse_args()
    if args.width <= 0 or (args.height is not None and args.height <= 0) or args.skip <= 0:
        parser.error("Dimensions and --skip must be positive")
    if not args.input.is_dir() or args.input.resolve() == args.output.resolve():
        parser.error("Use an existing input directory and a different output directory")
    images = sorted(p for p in args.input.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    args.output.mkdir(parents=True, exist_ok=True)
    for path in images[::args.skip]:
        target = args.output / path.name
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite {target}")
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image)
            height = args.height or max(1, round(image.height * args.width / image.width))
            ImageOps.contain(image, (args.width, height), Image.Resampling.LANCZOS).save(target)
    print(f"Saved {len(images[::args.skip])} images to {args.output}")


if __name__ == "__main__":
    main()
