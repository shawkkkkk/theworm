import os
import numpy as np

BUILD_PATH = os.path.join(os.path.dirname(__file__), "build", "graph.npz")


class WormBrain:
    def __init__(self, graph_path=BUILD_PATH, seed=0, dt=0.05, tau=0.5,
                 chem_scale=0.05, elec_scale=0.05):
        data = np.load(graph_path, allow_pickle=True)
        self.neurons = list(data["neurons"])
        self.name_to_idx = {n: i for i, n in enumerate(self.neurons)}
        chemical = data["chemical"].astype(np.float64)
        electrical = data["electrical"].astype(np.float64)
        n = len(self.neurons)

        rng = np.random.default_rng(seed)
        sign = rng.choice([-1.0, 1.0], size=chemical.shape)
        self.W_chem = chemical * sign * chem_scale
        self.W_elec = electrical * elec_scale
        self.elec_row_sum = self.W_elec.sum(axis=1)

        self.n = n
        self.dt = dt
        self.tau = tau
        self.activity = np.zeros(n)

    def idx(self, names):
        if isinstance(names, str):
            return self.name_to_idx[names]
        missing = [x for x in names if x not in self.name_to_idx]
        if missing:
            raise KeyError(f"neurons not found in connectome: {missing}")
        return [self.name_to_idx[x] for x in names]

    def reset(self):
        self.activity[:] = 0.0

    def step(self, external=None):
        s = np.tanh(self.activity)
        drive = self.W_chem.T @ s
        drive += self.W_elec @ self.activity - self.elec_row_sum * self.activity
        if external is not None:
            drive = drive + external
        d_activity = (-self.activity + np.tanh(drive)) / self.tau
        self.activity = self.activity + self.dt * d_activity
        return self.activity

    def run(self, steps, external=None):
        for _ in range(steps):
            self.step(external)
        return self.activity

    def _resolve(self, names_or_indices):
        if isinstance(names_or_indices, str):
            return self.idx(names_or_indices)
        if isinstance(names_or_indices, list) and names_or_indices and isinstance(names_or_indices[0], str):
            return self.idx(names_or_indices)
        return names_or_indices

    def inject(self, names_or_indices, value):
        indices = self._resolve(names_or_indices)
        external = np.zeros(self.n)
        if isinstance(indices, int):
            indices = [indices]
        for i in indices:
            external[i] = value
        return external

    def read(self, names_or_indices):
        indices = self._resolve(names_or_indices)
        if isinstance(indices, int):
            return float(self.activity[indices])
        return self.activity[indices]