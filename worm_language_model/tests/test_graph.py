import tempfile
import unittest
from pathlib import Path

import numpy as np

from worm_language_model.graph import (
    DEFAULT_GRAPH_PATH,
    WormConnectome,
    WormReservoir,
)


def write_graph(folder: str, *, cycle: bool = True) -> Path:
    names = np.array(["ASEL", "AIBL", "AVBL"])
    chemical = np.zeros((3, 3), dtype=np.int32)
    chemical[0, 1] = 4  # ASEL -> AIBL
    chemical[1, 2] = 2  # AIBL -> AVBL
    if cycle:
        chemical[2, 0] = 1
        chemical[0, 2] = 3  # A second AVBL input breaks relabeling symmetry.
    electrical = np.zeros((3, 3), dtype=np.int32)
    path = Path(folder) / "graph.npz"
    np.savez(path, neurons=names, chemical=chemical, electrical=electrical)
    return path


class ConnectomeTests(unittest.TestCase):
    def test_pre_to_post_orientation_and_normalization(self):
        with tempfile.TemporaryDirectory() as folder:
            graph = WormConnectome(write_graph(folder, cycle=False), require_302=False)
            self.assertEqual(graph.matrix[graph.index("AIBL"), graph.index("ASEL")], 1)
            self.assertEqual(graph.matrix[graph.index("AVBL"), graph.index("AIBL")], 1)
            self.assertEqual(graph.matrix[graph.index("ASEL"), graph.index("AIBL")], 0)

    def test_rejects_asymmetric_gap_junctions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = write_graph(folder)
            with np.load(path, allow_pickle=False) as data:
                names = data["neurons"]
                chemical = data["chemical"]
            electrical = np.zeros((3, 3), dtype=np.int32)
            electrical[0, 1] = 1
            np.savez(path, neurons=names, chemical=chemical, electrical=electrical)
            with self.assertRaisesRegex(ValueError, "symmetric"):
                WormConnectome(path, require_302=False)


class ReservoirTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.graph = WormConnectome(write_graph(self.folder.name), require_302=False)

    def tearDown(self):
        self.folder.cleanup()

    def test_same_seed_is_reproducible(self):
        values = np.random.default_rng(9).normal(size=(6, 8)).astype(np.float32)
        a = WormReservoir(self.graph, embedding_dim=8, feature_dim=5, seed=22)
        b = WormReservoir(self.graph, embedding_dim=8, feature_dim=5, seed=22)
        np.testing.assert_array_equal(a.sequence(values), b.sequence(values))

    def test_shuffled_control_is_reproducible_and_changes_path(self):
        values = np.random.default_rng(13).normal(size=(5, 8)).astype(np.float32)
        a = WormReservoir(self.graph, embedding_dim=8, feature_dim=5, seed=22)
        b = WormReservoir(self.graph, embedding_dim=8, feature_dim=5, seed=22)
        intact = a.sequence(values, mode="intact")
        shuffled_a = a.sequence(values, mode="shuffled")
        shuffled_b = b.sequence(values, mode="shuffled")
        np.testing.assert_array_equal(shuffled_a, shuffled_b)
        self.assertGreater(float(np.max(np.abs(intact - shuffled_a))), 1e-5)

    def test_no_edges_is_exactly_zero(self):
        model = WormReservoir(self.graph, embedding_dim=4, feature_dim=6)
        features = model.step(np.ones(4, dtype=np.float32), mode="no_edges")
        self.assertEqual(np.count_nonzero(model.state), 0)
        self.assertEqual(np.count_nonzero(features), 0)
        self.assertEqual(model.telemetry()["most_active"], [])

    def test_intact_graph_changes_state(self):
        model = WormReservoir(self.graph, embedding_dim=4, feature_dim=6)
        for _ in range(3):
            model.step(np.ones(4, dtype=np.float32))
        self.assertGreater(np.count_nonzero(model.state), 0)
        self.assertEqual(model.updates, 3)

    def test_sequence_reset_prevents_future_leakage(self):
        values = np.random.default_rng(3).normal(size=(7, 4)).astype(np.float32)
        model = WormReservoir(self.graph, embedding_dim=4, feature_dim=6)
        full = model.sequence(values)
        prefix = model.sequence(values[:3])
        np.testing.assert_array_equal(full[:3], prefix)


@unittest.skipUnless(DEFAULT_GRAPH_PATH.exists(), "Run python build_graph.py first")
class FullCookGraphTests(unittest.TestCase):
    def test_repository_graph_has_all_302_neurons(self):
        graph = WormConnectome()
        self.assertEqual(len(graph.neurons), 302)
        for name in ("ASEL", "ASER", "AVAL", "AVAR", "AVBL", "AVBR", "PVCL", "PVCR"):
            self.assertIsInstance(graph.index(name), int)


if __name__ == "__main__":
    unittest.main()
