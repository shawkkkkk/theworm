# Worm Language Model

> **Phase 1: connectome reservoir implemented. Chat generation is not trained or deployed yet.**

The Worm Language Model (WLM) is a side experiment inside TheWorm. It asks a narrow question:

> Can the fixed 302-neuron *C. elegans* connectome provide a measurable, causal signal that changes the predictions of a frozen language model?

It follows the broad architecture demonstrated by [nftechie/flm](https://github.com/nftechie/flm), replacing the fly graph with the Cook et al. 2019 adult-hermaphrodite worm graph.

## What “worm language model” would actually mean

```text
frozen pretrained language model
          │ token embeddings
          ▼
fixed 302-node worm connectome reservoir
          │ 64 numerical features
          ▼
small trained readout
          │ bounded logit adjustment
          ▼
next-token prediction
```

The pretrained language model supplies vocabulary, grammar, facts, and most of the response quality. The worm graph supplies an additional stateful signal. Only a small readout would be trained; the anatomical graph and language backbone would stay fixed.

That is very different from claiming that a biological worm understands or produces language. A 302-neuron connectome alone is not ChatGPT.

## What works now

- `graph.py` reads `build/graph.npz`, which is generated from OpenWorm’s `Cook2019HermReader`.
- Chemical connections are directed from presynaptic to postsynaptic neurons.
- Electrical connections are included in both directions.
- Incoming contact counts are normalized for stable recurrence.
- Every stand-in token produces one causal graph update.
- Fixed, seeded input/output interfaces map embeddings into 302 nodes and pool them into 64 features.
- `intact`, `shuffled`, and `no_edges` modes provide basic causal controls.
- Unit tests verify direction, normalization, reproducibility, reset behavior, disconnection, and the full 302-neuron graph.

The states are abstract numbers. They are not membrane potentials, spikes, neurotransmitter effects, biological time, thoughts, or feelings.

## Run the Phase 1 demo

From the repository root:

```bash
python build_graph.py
python -m worm_language_model.demo "hello from the worm"
```

Compare it with a disconnected graph:

```bash
python -m worm_language_model.demo "hello from the worm" --mode no_edges
```

Run the tests:

```bash
python -m unittest discover -s worm_language_model/tests -p 'test_*.py' -v
```

The demo uses deterministic hash-derived vectors so it can test the graph without downloading a large language model. It does not generate text.

## What comes next

1. Pin a small frozen instruction-tuned language backbone and its license.
2. Feed its real token embeddings through the worm reservoir.
3. Train a small, bounded adapter only on assistant next-token targets.
4. Add a parameter-matched direct-input baseline.
5. Evaluate intact, disconnected, and relabeled worm wiring on held-out conversations.
6. Publish the training manifest, graph fingerprint, split selection, and results.
7. Deploy inference behind the disabled chat interface at `site/web/wlm.html` only if the model passes the checks.

The critical result will not be whether WLM can produce a funny answer. It will be whether the trained worm pathway has a reproducible effect and how that effect compares with the controls.

## Attribution

The reservoir design was independently adapted from the ideas and MIT-licensed implementation in [FLM — Fly Language Model](https://github.com/nftechie/flm) by Alex Wormuth. See `THIRD_PARTY_NOTICES.md`.

The worm connectivity comes from Cook SJ et al. (2019), [“Whole-animal connectomes of both *Caenorhabditis elegans* sexes”](https://pubmed.ncbi.nlm.nih.gov/31270481/), accessed through OpenWorm’s [C. elegans Connectome Toolbox](https://github.com/openworm/ConnectomeToolbox).

