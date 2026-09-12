"""
build_positions.py

Extracts real, measured 3D soma coordinates for all 302 neurons from c302's
bundled NeuroML2 cell files. These positions trace back to WormBase's
VirtualWorm Blender model (Grove & Sternberg, Caltech) -- the same source
OpenWorm's own 3D viewer uses. Every neuron in the connectome graph has a
matching file, so nothing here is estimated -- it's the real anatomical
layout, same role as the fly project's soma-coordinate feather file.
"""
import os
import re
import numpy as np
import c302

ROOT = os.path.dirname(__file__)
GRAPH_PATH = os.path.join(ROOT, "build", "graph.npz")
OUT_PATH = os.path.join(ROOT, "build", "positions.npz")
NEUROML2_DIR = os.path.join(os.path.dirname(c302.__file__), "NeuroML2")

SOMA_RE = re.compile(
    r'<segment id="0"[^>]*>\s*<proximal x="([-\d.]+)" y="([-\d.]+)" z="([-\d.]+)"'
)


def main():
    graph = np.load(GRAPH_PATH, allow_pickle=True)
    names = list(graph["neurons"])

    xyz = np.zeros((len(names), 3), dtype=np.float32)
    missing = []
    for i, name in enumerate(names):
        path = os.path.join(NEUROML2_DIR, f"{name}.cell.nml")
        try:
            with open(path) as f:
                content = f.read()
        except FileNotFoundError:
            missing.append(name)
            continue
        m = SOMA_RE.search(content)
        if not m:
            missing.append(name)
            continue
        xyz[i] = [float(v) for v in m.groups()]

    if missing:
        print(f"WARNING: {len(missing)} neurons had no position: {missing}")
    else:
        print(f"all {len(names)} neurons matched to real measured soma coordinates")

    np.savez(OUT_PATH, neurons=np.array(names), xyz=xyz)
    print(f"-> {OUT_PATH}")


if __name__ == "__main__":
    main()