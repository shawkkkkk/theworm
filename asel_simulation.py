"""
asel_simulation.py

Builds a small real-connectome subcircuit around the C. elegans salt-sensing
neurons (ASEL/ASER), stimulates them with an injected current, and records
what the command interneurons that drive locomotion (AVA/AVB/PVC) do in
response -- using c302's parameter set C1 (single-compartment,
conductance-based cells with graded/analog synapses), which is the
physiologically appropriate choice for C. elegans: unlike the fly, these
neurons don't spike, they signal with continuous graded potentials.

Every cell and connection below comes from the Cook et al. 2019 connectome
via c302's cect data reader -- nothing here is invented. What IS a choice:
which subset of the 302-neuron connectome to include, and which cell to
call the "sensory input."
"""
import c302
from c302.parameters_C1 import ParameterisedModel
from pyneuroml import pynml

TARGET_DIR = "examples"
REFERENCE = "c302_C1_ASEL"

CELLS = [
    "ASEL", "ASER",
    "AWCL", "AWCR",
    "AIBL", "AIBR",
    "AIYL", "AIYR",
    "ASHL", "ASHR",
    "AVAL", "AVAR",
    "AVBL", "AVBR",
    "PVCL", "PVCR",
]

CELLS_TO_STIMULATE = ["ASEL", "ASER"]


def main():
    params = ParameterisedModel()

    params.set_bioparameter(
        "unphysiological_offset_current", "5pA", "ASEL/ASER stimulus", "0"
    )
    params.set_bioparameter(
        "unphysiological_offset_current_del", "100ms", "ASEL/ASER stimulus", "0"
    )
    params.set_bioparameter(
        "unphysiological_offset_current_dur", "600ms", "ASEL/ASER stimulus", "0"
    )

    c302.generate(
        REFERENCE,
        params,
        cells=CELLS,
        cells_to_stimulate=CELLS_TO_STIMULATE,
        duration=800,
        dt=0.05,
        target_directory=TARGET_DIR,
        verbose=True,
    )

    lems_file = f"{TARGET_DIR}/LEMS_{REFERENCE}.xml"
    print(f"\nrunning {lems_file} ...")
    pynml.run_lems_with_jneuroml(lems_file, nogui=True, load_saved_data=False)

    print("\nreloading traces ...")
    traces = pynml.reload_saved_data(lems_file, base_dir=".", reload_traces=True)

    print("\n======================================")
    print("   ASEL/ASER STIMULUS -> COMMAND NEURON RESPONSE")
    print("======================================\n")

    readout = ["AVAL", "AVAR", "AVBL", "AVBR", "PVCL", "PVCR"]
    for cell in readout:
        key = next((k for k in traces if k.split("/")[0] == cell), None)
        if key is None:
            print(f"  {cell}: no trace found")
            continue
        v = traces[key]
        baseline = sum(v[:20]) / 20
        peak = max(v)
        print(f"  {cell:6s}  baseline={baseline*1000:7.2f} mV   "
              f"peak={peak*1000:7.2f} mV   delta={((peak-baseline)*1000):+7.2f} mV")

    print(f"\nfull traces are in {TARGET_DIR}/*.dat")


if __name__ == "__main__":
    main()