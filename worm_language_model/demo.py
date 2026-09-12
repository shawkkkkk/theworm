"""Exercise the worm reservoir with deterministic stand-in token vectors.

This proves that token-sized inputs causally traverse the 302-node graph. It
does not generate prose. A frozen language backbone and trained readout are a
later milestone.
"""

from __future__ import annotations

import argparse
import hashlib

import numpy as np

from .graph import WormConnectome, WormReservoir


def stand_in_embedding(token: str, dimensions: int) -> np.ndarray:
    """Return a stable test vector without downloading a language model."""
    raw = hashlib.shake_256(token.encode("utf-8")).digest(dimensions)
    values = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
    values = (values - 127.5) / 127.5
    rms = float(np.sqrt(np.mean(values * values)))
    return values / max(rms, 1e-6)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", default="hello from the worm")
    parser.add_argument("--mode", choices=WormReservoir.MODES, default="intact")
    parser.add_argument("--embedding-dim", type=int, default=64)
    args = parser.parse_args()

    tokens = args.text.split()
    if not tokens:
        parser.error("Text must contain at least one token.")

    graph = WormConnectome()
    reservoir = WormReservoir(graph, embedding_dim=args.embedding_dim)

    print("\nWORM LANGUAGE MODEL — RESERVOIR CHECK")
    print("This is a graph test, not language generation.\n")
    print(f"neurons: {len(graph.neurons)}")
    print(f"mode: {args.mode}")
    print(f"graph fingerprint: {graph.fingerprint[:16]}…\n")

    for token in tokens:
        features = reservoir.step(
            stand_in_embedding(token, args.embedding_dim), mode=args.mode
        )
        info = reservoir.telemetry(top_k=3)
        names = ", ".join(item["neuron"] for item in info["most_active"])
        print(
            f"{token!r:<20} state_rms={info['state_rms']:.5f} "
            f"feature_rms={np.sqrt(np.mean(features * features)):.5f} "
            f"top={names or 'none'}"
        )

    print("\nNext milestone: connect real token embeddings and train a bounded readout.")


if __name__ == "__main__":
    main()

