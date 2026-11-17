"""COLMAP preprocessing followed by training; extra options go to train.py."""
import argparse
from pathlib import Path
from utils.local_tools import PROJECT_ROOT, run_python, validate_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_path", "-s", default=str(PROJECT_ROOT / "data"))
    parser.add_argument("--model_path", "-m")
    parser.add_argument("--skip_conversion", action="store_true")
    parser.add_argument("--no_gpu", action="store_true", help="CPU COLMAP only; training still uses CUDA")
    parser.add_argument("--camera", default="OPENCV")
    args, training_options = parser.parse_known_args()
    source = Path(args.source_path).expanduser().resolve()
    if not args.skip_conversion:
        options = ["-s", str(source), "--camera", args.camera]
        if args.no_gpu:
            options.append("--no_gpu")
        run_python("convert.py", options)
    validate_dataset(source)
    model = Path(args.model_path).resolve() if args.model_path else PROJECT_ROOT / "output" / source.name
    run_python("train.py", ["-s", str(source), "-m", str(model), *training_options])


if __name__ == "__main__":
    main()
