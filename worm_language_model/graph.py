"""A fixed C. elegans connectome reservoir for token-by-token experiments.

The anatomical graph is real; the recurrence below is an abstract numerical
model. It is not a simulation of membrane voltages, neurotransmitters,
biological time, understanding, or consciousness.

The graph written by ``build_graph.py`` stores chemical[pre, post] and a
bidirectional electrical matrix. This module transposes those arrays into
W[post, pre], combines their unsigned contact counts, and normalizes every
postsynaptic row by its total incoming weight.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH_PATH = ROOT / "build" / "graph.npz"


class WormConnectome:
    """Load and validate the graph produced from Cook2019HermReader."""

    def __init__(self, path: str | Path = DEFAULT_GRAPH_PATH, require_302: bool = True):
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(
                f"Connectome graph not found at {self.path}. "
                "Run `python build_graph.py` from the repository root first."
            )

        with np.load(self.path, allow_pickle=False) as data:
            required = {"neurons", "chemical", "electrical"}
            missing = required.difference(data.files)
            if missing:
                raise ValueError(f"Graph archive is missing: {sorted(missing)}")
            neurons = np.asarray(data["neurons"]).astype(str)
            chemical = np.asarray(data["chemical"], dtype=np.float32)
            electrical = np.asarray(data["electrical"], dtype=np.float32)

        if neurons.ndim != 1 or len(set(neurons.tolist())) != len(neurons):
            raise ValueError("Neuron names must be a unique one-dimensional list.")
        if require_302 and len(neurons) != 302:
            raise ValueError(f"Expected 302 neurons, found {len(neurons)}.")
        expected_shape = (len(neurons), len(neurons))
        if chemical.shape != expected_shape or electrical.shape != expected_shape:
            raise ValueError(
                f"Connection arrays must both have shape {expected_shape}; "
                f"found {chemical.shape} and {electrical.shape}."
            )
        if not np.isfinite(chemical).all() or not np.isfinite(electrical).all():
            raise ValueError("Connection arrays contain non-finite values.")
        if (chemical < 0).any() or (electrical < 0).any():
            raise ValueError("Connection counts must be non-negative.")
        if not np.allclose(electrical, electrical.T):
            raise ValueError("The electrical connection matrix must be symmetric.")

        # build_graph.py stores rows as presynaptic and columns as postsynaptic.
        # Reservoir multiplication needs rows as postsynaptic so information
        # moves from state[pre] to next_state[post].
        incoming = chemical.T + electrical.T
        row_totals = incoming.sum(axis=1, keepdims=True)
        self.matrix = np.divide(
            incoming,
            row_totals,
            out=np.zeros_like(incoming, dtype=np.float32),
            where=row_totals > 0,
        ).astype(np.float32, copy=False)

        self.neurons = tuple(neurons.tolist())
        self.name_to_index = {name: i for i, name in enumerate(self.neurons)}
        self.chemical_edges = int(np.count_nonzero(chemical))
        self.electrical_directed_edges = int(np.count_nonzero(electrical))
        self.fingerprint = self._fingerprint(neurons, chemical, electrical)

    @staticmethod
    def _fingerprint(*arrays: np.ndarray) -> str:
        digest = hashlib.sha256()
        for array in arrays:
            contiguous = np.ascontiguousarray(array)
            digest.update(str(contiguous.dtype).encode())
            digest.update(np.asarray(contiguous.shape, dtype=np.int64).tobytes())
            digest.update(contiguous.tobytes())
        return digest.hexdigest()

    def index(self, name: str) -> int:
        try:
            return self.name_to_index[name.upper()]
        except KeyError as exc:
            raise KeyError(f"Neuron {name!r} is not in this graph.") from exc

    def summary(self) -> dict[str, object]:
        return {
            "neurons": len(self.neurons),
            "chemical_edges": self.chemical_edges,
            "electrical_directed_edges": self.electrical_directed_edges,
            "orientation": "row=postsynaptic, column=presynaptic",
            "weights": "unsigned incoming-normalized contact counts",
            "fingerprint": self.fingerprint,
        }


class WormReservoir:
    """One causal graph update per token embedding.

    This follows the broad experimental pattern used by nftechie/flm while
    remaining deliberately small and transparent:

        x_t = tanh(W @ (r*x_(t-1) + g*B*embedding_t))

    B and the output pooling map are fixed, seeded interfaces. They are not
    anatomical language pathways. No parameter in the worm graph is trained.
    """

    MODES = ("intact", "no_edges", "shuffled")

    def __init__(
        self,
        graph: WormConnectome,
        embedding_dim: int,
        feature_dim: int = 64,
        seed: int = 302,
        recurrence_gain: float = 0.6,
        input_gain: float = 0.4,
    ):
        if embedding_dim < 1 or feature_dim < 1:
            raise ValueError("Embedding and feature dimensions must be positive.")
        if recurrence_gain < 0 or input_gain < 0:
            raise ValueError("Reservoir gains must be non-negative.")

        self.graph = graph
        self.n = len(graph.neurons)
        self.embedding_dim = embedding_dim
        self.feature_dim = feature_dim
        self.seed = seed
        self.recurrence_gain = float(recurrence_gain)
        self.input_gain = float(input_gain)

        rng = np.random.default_rng(seed)
        self.input_projection = (
            rng.standard_normal((embedding_dim, feature_dim)) / np.sqrt(embedding_dim)
        ).astype(np.float32)
        self.input_bins = rng.integers(0, feature_dim, self.n)
        self.input_signs = rng.choice(np.array([-1.0, 1.0], np.float32), self.n)
        self.output_bins = rng.integers(0, feature_dim, self.n)
        self.output_signs = rng.choice(np.array([-1.0, 1.0], np.float32), self.n)
        self.output_scale = np.sqrt(
            np.maximum(1, np.bincount(self.output_bins, minlength=feature_dim))
        ).astype(np.float32)
        self.permutation = rng.permutation(self.n)
        self.inverse_permutation = np.argsort(self.permutation)

        self.state = np.zeros(self.n, dtype=np.float32)
        self.updates = 0

    def reset(self) -> None:
        self.state.fill(0)
        self.updates = 0

    def project_input(self, embedding: np.ndarray) -> np.ndarray:
        embedding = np.asarray(embedding, dtype=np.float32)
        if embedding.shape != (self.embedding_dim,):
            raise ValueError(
                f"Expected embedding shape {(self.embedding_dim,)}, "
                f"found {embedding.shape}."
            )
        code = embedding @ self.input_projection
        rms = float(np.sqrt(np.mean(code * code)))
        return code / max(rms, 1e-6)

    def _pool(self) -> np.ndarray:
        features = np.bincount(
            self.output_bins,
            weights=self.state * self.output_signs,
            minlength=self.feature_dim,
        ).astype(np.float32)
        features /= self.output_scale
        rms = float(np.sqrt(np.mean(features * features)))
        if rms <= 1e-6:
            return np.zeros(self.feature_dim, dtype=np.float32)
        return features / rms

    def step(self, embedding: np.ndarray, mode: str = "intact") -> np.ndarray:
        if mode not in self.MODES:
            raise ValueError(f"Mode must be one of {self.MODES}; found {mode!r}.")

        code = self.project_input(embedding)
        drive = (
            self.recurrence_gain * self.state
            + self.input_gain * code[self.input_bins] * self.input_signs
        )

        if mode == "no_edges":
            self.state.fill(0)
        elif mode == "shuffled":
            relabeled = self.graph.matrix @ drive[self.permutation]
            self.state = np.tanh(relabeled[self.inverse_permutation]).astype(np.float32)
        else:
            self.state = np.tanh(self.graph.matrix @ drive).astype(np.float32)

        self.updates += 1
        return self._pool()

    def sequence(self, embeddings: np.ndarray, mode: str = "intact") -> np.ndarray:
        values = np.asarray(embeddings, dtype=np.float32)
        if values.ndim != 2 or values.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Expected a token-by-{self.embedding_dim} embedding matrix; "
                f"found {values.shape}."
            )
        self.reset()
        if len(values) == 0:
            return np.empty((0, self.feature_dim), dtype=np.float32)
        return np.stack([self.step(value, mode) for value in values])

    def telemetry(self, top_k: int = 8) -> dict[str, object]:
        count = max(0, min(int(top_k), self.n))
        active = np.flatnonzero(np.abs(self.state) > 1e-8)
        if count and len(active):
            ranked = active[np.argsort(np.abs(self.state[active]))[::-1]]
            order = ranked[:count]
        else:
            order = []
        return {
            "updates": self.updates,
            "state_rms": float(np.sqrt(np.mean(self.state * self.state))),
            "units": "abstract reservoir state",
            "most_active": [
                {"neuron": self.graph.neurons[i], "state": float(self.state[i])}
                for i in order
            ],
        }
