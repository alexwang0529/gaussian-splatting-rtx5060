"""Launch the project-local SIBR viewer with a trained model directory."""
import argparse
from pathlib import Path
from utils.local_tools import resolve_tool, run_checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_path", "-m", type=Path, required=True)
    args = parser.parse_args()
    model = args.model_path.resolve()
    if not (model / "point_cloud").is_dir():
        parser.error("-m must be a trained model directory containing point_cloud")
    viewer = resolve_tool("viewer")
    run_checked([viewer, "-m", model], cwd=viewer.parent)


if __name__ == "__main__":
    main()
