"""Extract frames, run COLMAP, then train with the current Python interpreter."""
import argparse
from pathlib import Path
from utils.local_tools import PROJECT_ROOT, resolve_tool, run_checked, run_python


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", default=str(PROJECT_ROOT / "data/test.mp4"))
    parser.add_argument("--source_path", "-s")
    parser.add_argument("--model_path", "-m")
    parser.add_argument("--fps", type=float, default=4.0)
    parser.add_argument("--skip_extraction", action="store_true")
    parser.add_argument("--skip_conversion", action="store_true")
    parser.add_argument("--no_gpu", action="store_true", help="CPU COLMAP only; training still uses CUDA")
    args, training_options = parser.parse_known_args()
    video = Path(args.video).expanduser().resolve()
    source = Path(args.source_path).resolve() if args.source_path else video.parent / video.stem
    if args.fps <= 0:
        parser.error("--fps must be positive")
    if args.skip_conversion and not args.skip_extraction:
        parser.error("--skip_conversion requires --skip_extraction: new frames must not use old poses")
    images = source / "input"
    if not args.skip_extraction:
        if not video.is_file():
            parser.error(f"Video not found: {video}")
        if images.is_dir() and any(images.iterdir()):
            parser.error("Input already contains frames. Use a new -s directory or --skip_extraction.")
        if any((source / name).exists() for name in ("distorted/database.db", "sparse/0")):
            parser.error("Dataset already contains a reconstruction. Use a new -s directory.")
        images.mkdir(parents=True, exist_ok=True)
        run_checked([resolve_tool("ffmpeg"), "-nostdin", "-n", "-i", video,
            "-qscale:v", "1", "-qmin", "1", "-vf", f"fps={args.fps}", images / "%04d.jpg"])
    if not images.is_dir() or not any(images.iterdir()):
        parser.error(f"No extracted frames in {images}")
    options = ["-s", str(source)]
    if args.model_path:
        options.extend(["-m", str(Path(args.model_path).resolve())])
    if args.skip_conversion:
        options.append("--skip_conversion")
    if args.no_gpu:
        options.append("--no_gpu")
    run_python("train_images.py", [*options, *training_options])


if __name__ == "__main__":
    main()
