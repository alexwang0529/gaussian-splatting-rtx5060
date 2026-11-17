"""Export Gaussian centers and approximate RGB colors as a standard PLY cloud."""
import argparse
from pathlib import Path
import tempfile

import numpy as np
from plyfile import PlyData, PlyElement

from utils.sh_utils import SH2RGB


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", type=Path, required=True)
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument("--ascii", action="store_true", help="Write text PLY instead of binary PLY")
    args = parser.parse_args()
    source = args.input.expanduser().resolve()
    destination = args.output.expanduser().resolve()
    if source == destination:
        parser.error("Input and output must be different files")
    vertices = PlyData.read(str(source))["vertex"].data
    fields = set(vertices.dtype.names)
    if not {"x", "y", "z"} <= fields:
        parser.error("Input PLY must contain x, y and z vertex coordinates")
    if {"f_dc_0", "f_dc_1", "f_dc_2"} <= fields:
        coefficients = np.column_stack([vertices[f"f_dc_{i}"] for i in range(3)])
        rgb = np.rint(np.clip(SH2RGB(coefficients), 0.0, 1.0) * 255).astype(np.uint8)
        color_method = "zero-order spherical harmonic RGB approximation"
    elif {"red", "green", "blue"} <= fields:
        rgb = np.column_stack([vertices[name] for name in ("red", "green", "blue")])
        color_method = "existing RGB vertex colors"
    else:
        parser.error("Input needs f_dc_0/1/2 Gaussian colors or red/green/blue vertex colors")
    coordinates = np.column_stack([vertices[name] for name in ("x", "y", "z")])
    if not np.isfinite(coordinates).all():
        parser.error("Input contains non-finite point coordinates")
    cloud = np.empty(len(vertices), dtype=[
        ("x", "f4"), ("y", "f4"), ("z", "f4"),
        ("red", "u1"), ("green", "u1"), ("blue", "u1"),
    ])
    for axis in ("x", "y", "z"):
        cloud[axis] = vertices[axis]
    for index, channel in enumerate(("red", "green", "blue")):
        cloud[channel] = rgb[:, index]
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".ply.tmp", delete=False) as handle:
            temporary_path = Path(handle.name)
            PlyData([PlyElement.describe(cloud, "vertex")], text=args.ascii,
                    byte_order="<", comments=["Gaussian centers with approximate RGB colors"]).write(handle)
        temporary_path.replace(destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    print(f"Saved {len(cloud)} points to {destination}")
    print(f"Colors use {color_method}")


if __name__ == "__main__":
    main()
