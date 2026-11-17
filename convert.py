#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#
"""Run COLMAP using project-local tools and checked subprocesses."""
import argparse
from pathlib import Path
import shutil
from utils.local_tools import resolve_tool, run_checked


def main():
    parser = argparse.ArgumentParser("COLMAP converter")
    parser.add_argument("--no_gpu", action="store_true")
    parser.add_argument("--skip_matching", action="store_true")
    parser.add_argument("--source_path", "-s", required=True)
    parser.add_argument("--camera", default="OPENCV")
    parser.add_argument("--colmap_executable", default="")
    parser.add_argument("--resize", action="store_true")
    parser.add_argument("--magick_executable", default="")
    args = parser.parse_args()
    source = Path(args.source_path).expanduser().resolve()
    if not (source / "input").is_dir():
        parser.error(f"Input images directory not found: {source / 'input'}")
    colmap = resolve_tool("colmap", args.colmap_executable)
    magick = resolve_tool("magick", args.magick_executable) if args.resize else None

    def run(*arguments):
        # COLMAP 3.8 SQLite needs relative paths for Chinese Windows directories.
        run_checked([colmap, *arguments], cwd=source, colmap=True)

    if not args.skip_matching:
        (source / "distorted/sparse").mkdir(parents=True, exist_ok=True)
        run("feature_extractor", "--database_path", "distorted/database.db",
            "--image_path", "input", "--ImageReader.single_camera", "1",
            "--ImageReader.camera_model", args.camera,
            "--SiftExtraction.use_gpu", "0" if args.no_gpu else "1")
        run("exhaustive_matcher", "--database_path", "distorted/database.db",
            "--SiftMatching.use_gpu", "0" if args.no_gpu else "1")
        run("mapper", "--database_path", "distorted/database.db",
            "--image_path", "input", "--output_path", "distorted/sparse",
            "--Mapper.ba_global_function_tolerance", "0.000001")
    if not (source / "distorted/sparse/0").is_dir():
        raise FileNotFoundError("No distorted/sparse/0 model; training was not started.")
    run("image_undistorter", "--image_path", "input",
        "--input_path", "distorted/sparse/0", "--output_path", ".",
        "--output_type", "COLMAP")
    sparse = source / "sparse"
    (sparse / "0").mkdir(exist_ok=True)
    for path in sparse.iterdir():
        if path.is_file():
            path.replace(sparse / "0" / path.name)
    if args.resize:
        for factor, percentage in ((2, "50%"), (4, "25%"), (8, "12.5%")):
            destination = source / f"images_{factor}"
            destination.mkdir(exist_ok=True)
            for image in (source / "images").iterdir():
                if image.is_file():
                    target = destination / image.name
                    shutil.copy2(image, target)
                    run_checked([magick, "mogrify", "-resize", percentage, target], cwd=source)
    print("COLMAP preprocessing complete.")


if __name__ == "__main__":
    main()
