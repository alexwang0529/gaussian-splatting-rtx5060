"""Resolve project-local tools and run checked subprocesses."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_tool(name, explicit=None):
    bundled = {
        "colmap": "external/COLMAP-3.8-windows-cuda/bin/colmap.exe",
        "ffmpeg": "external/ffmpeg/bin/ffmpeg.exe",
        "magick": "external/ImageMagick-7.1.1-Q16-HDRI/magick.exe",
        "viewer": "external/viewers/bin/SIBR_gaussianViewer_app.exe",
        "remote_viewer": "external/viewers/bin/SIBR_remoteGaussian_app.exe",
    }
    path = Path(explicit).expanduser() if explicit else PROJECT_ROOT / bundled[name]
    if not path.is_file():
        found = shutil.which(str(explicit or name))
        if not found:
            raise FileNotFoundError(f"Missing {name} executable: {path}")
        path = Path(found)
    path = path.resolve()
    if name == "colmap" and path.suffix.lower() in (".bat", ".cmd"):
        native = path.parent / "bin/colmap.exe"
        if native.is_file():
            path = native
    return path


def run_checked(command, cwd=PROJECT_ROOT, colmap=False):
    command = [str(part) for part in command]
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    if colmap:
        library = Path(command[0]).parent.parent / "lib"
        if library.is_dir():
            env["PATH"] = str(library) + os.pathsep + env.get("PATH", "")
            env["QT_PLUGIN_PATH"] = str(library / "plugins")
    print("Running:", subprocess.list2cmdline(command), flush=True)
    subprocess.run(command, cwd=str(cwd), env=env, check=True)


def run_python(script, arguments):
    run_checked([sys.executable, PROJECT_ROOT / script, *arguments])


def validate_dataset(source):
    source = Path(source).resolve()
    if not (source / "images").is_dir():
        raise FileNotFoundError(f"Missing undistorted images: {source / 'images'}")
    sparse = source / "sparse/0"
    binary = all((sparse / n).is_file() for n in ("cameras.bin", "images.bin", "points3D.bin"))
    text = all((sparse / n).is_file() for n in ("cameras.txt", "images.txt", "points3D.txt"))
    if not (binary or text):
        raise FileNotFoundError(f"Incomplete COLMAP model: {sparse}")
    return source
