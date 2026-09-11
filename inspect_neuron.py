from cect.readers.Cook2019HermReader import get_instance
import sys

dataset = get_instance()

neuron = sys.argv[1].upper() if len(sys.argv) > 1 else "ASEL"

neurons, _ = dataset.get_neuron_to_neuron_conns()

if neuron not in neurons:
    print(f"{neuron} is not in the 302-neuron connectome.")
    raise SystemExit(1)

connections = dataset.get_current_connection_info_list()

outgoing = [
    c for c in connections
    if c.pre_cell == neuron and c.post_cell in neurons
]

incoming = [
    c for c in connections
    if c.post_cell == neuron and c.pre_cell in neurons
]

outgoing.sort(key=lambda c: float(c.number), reverse=True)
incoming.sort(key=lambda c: float(c.number), reverse=True)

print()
print("======================================")
print(f"       THEWORM — {neuron}")
print("======================================")
print()

print(f"Outgoing connections: {len(outgoing)}")
print()

for c in outgoing[:25]:
    print(
        f"  {neuron:5} -> {c.post_cell:5}"
        f"   weight={float(c.number):6.1f}"
        f"   class={c.synclass}"
    )

print()
print(f"Incoming connections: {len(incoming)}")
print()

for c in incoming[:25]:
    print(
        f"  {c.pre_cell:5} -> {neuron:5}"
        f"   weight={float(c.number):6.1f}"
        f"   class={c.synclass}"
    )

print()
