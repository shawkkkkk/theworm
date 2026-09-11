from cect.readers.Cook2019HermReader import get_instance

print()
print("Loading the real C. elegans connectome...")
print("Dataset: Cook et al. 2019 hermaphrodite")
print()

dataset = get_instance()

neurons, neuron_connections = dataset.get_neuron_to_neuron_conns()

print("====================================")
print("       THEWORM CONNECTOME CHECK")
print("====================================")
print()

print(f"Neurons found: {len(neurons)}")
print(f"Neuron-to-neuron connection records: {len(neuron_connections)}")
print()

print("Checking important neurons:")

important = [
    "ASEL",
    "ASER",
    "AVAL",
    "AVAR",
    "AVBL",
    "AVBR",
    "PVCL",
    "PVCR",
]

for neuron in important:
    status = "FOUND" if neuron in neurons else "MISSING"
    print(f"  {neuron}: {status}")

print()

if len(neurons) == 302:
    print("SUCCESS")
    print("The real 302-neuron C. elegans connectome is loaded.")
else:
    print(f"WARNING: Expected 302 neurons but found {len(neurons)}.")

print()
print("Synapse classes:")
for synapse_class in dataset.connections:
    print(f"  {synapse_class}")
