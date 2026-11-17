"""Launch the legacy remote viewer with an ASCII relative dataset path."""
import argparse
import os
from pathlib import Path
from utils.local_tools import PROJECT_ROOT, resolve_tool, run_checked, validate_dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_path", "-s", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6009)
    args = parser.parse_args()
    source = validate_dataset(args.source_path)
    # The old Windows viewer treats the UTF-8 absolute path from the network
    # as ANSI. Override it using an ASCII path relative to a fixed project cwd.
    relative = os.path.relpath(source, PROJECT_ROOT)
    if os.name == "nt" and not relative.isascii():
        parser.error("Use an ASCII dataset folder name under this project, e.g. data/test_run2. The project root itself may contain Chinese.")
    viewer = resolve_tool("remote_viewer")
    run_checked([viewer, "-s", relative, "--ip", args.ip, "--port", str(args.port)], cwd=PROJECT_ROOT)


if __name__ == "__main__":
    main()
