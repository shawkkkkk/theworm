import os
import numpy as np
from cect.readers.Cook2019HermReader import get_instance

OUT_DIR = os.path.join(os.path.dirname(__file__), "build")
OUT_PATH = os.path.join(OUT_DIR, "graph.npz")


def main():
    dataset = get_instance()
    neurons, conns = dataset.get_neuron_to_neuron_conns()
    names = sorted(neurons)
    index = {n: i for i, n in enumerate(names)}
    n = len(names)

    chemical = np.zeros((n, n), dtype=np.int32)
    electrical = np.zeros((n, n), dtype=np.int32)
    skipped = 0

    for c in conns:
        if c.pre_cell not in index or c.post_cell not in index:
            continue
        i, j = index[c.pre_cell], index[c.post_cell]
        weight = int(round(c.number))
        if c.synclass == "Generic_CS":
            chemical[i, j] += weight
        elif c.synclass == "Generic_GJ":
            electrical[i, j] += weight
            electrical[j, i] += weight
        else:
            skipped += 1
            continue

    os.makedirs(OUT_DIR, exist_ok=True)
    np.savez(OUT_PATH, neurons=np.array(names), chemical=chemical,
              electrical=electrical)

    print(f"neurons: {n}")
    print(f"chemical synapse edges: {int((chemical > 0).sum())}")
    print(f"gap junction pairs: {int((electrical > 0).sum()) // 2}")
    print(f"-> {OUT_PATH}")
    print(f"skipped (unclassified synapse type): {skipped}")


if __name__ == "__main__":
    main()