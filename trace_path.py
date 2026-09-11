from cect.readers.Cook2019HermReader import get_instance
import networkx as nx
import sys

dataset = get_instance()

source = sys.argv[1].upper() if len(sys.argv) > 1 else "ASEL"

targets = (
    [x.upper() for x in sys.argv[2:]]
    if len(sys.argv) > 2
    else ["AVAL", "AVAR", "AVBL", "AVBR", "PVCL", "PVCR"]
)

neurons, _ = dataset.get_neuron_to_neuron_conns()
neuron_set = set(neurons)

G = nx.DiGraph()

for neuron in neurons:
    G.add_node(neuron)

connections = dataset.get_current_connection_info_list()

for c in connections:

    if c.pre_cell not in neuron_set or c.post_cell not in neuron_set:
        continue

    strength = float(c.number)

    if c.synclass == "Generic_CS":

        if G.has_edge(c.pre_cell, c.post_cell):
            G[c.pre_cell][c.post_cell]["strength"] += strength
        else:
            G.add_edge(
                c.pre_cell,
                c.post_cell,
                strength=strength,
                kind="chemical"
            )

    elif c.synclass == "Generic_GJ":

        # Gap junctions are electrical and effectively bidirectional
        for a, b in [
            (c.pre_cell, c.post_cell),
            (c.post_cell, c.pre_cell)
        ]:

            if G.has_edge(a, b):
                G[a][b]["strength"] += strength
            else:
                G.add_edge(
                    a,
                    b,
                    strength=strength,
                    kind="gap"
                )

print()
print("======================================")
print("       THEWORM — PATH TRACER")
print("======================================")
print()

print(f"Source neuron: {source}")
print()

for target in targets:

    print(f"Path to {target}:")

    try:
        path = nx.shortest_path(G, source, target)

        print(f"  hops: {len(path) - 1}")
        print()

        for a, b in zip(path, path[1:]):

            edge = G[a][b]

            print(
                f"  {a:5} -> {b:5}"
                f"    strength={edge['strength']:.1f}"
                f"    type={edge['kind']}"
            )

        print()

    except nx.NetworkXNoPath:
        print("  No path found.")
        print()

