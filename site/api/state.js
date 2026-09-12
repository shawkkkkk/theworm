// Public, read-only project status for the TheWorm website.
//
// No wallet, private key, RPC call, or transaction path exists here. The token
// has not launched, so this endpoint deliberately reports build state instead
// of querying the unrelated contract inherited from the upstream fly project.

const state = {
  ok: true,
  project: 'TheWorm',
  phase: 'development',
  connectome: {
    source: 'Cook et al. 2019 hermaphrodite',
    neurons: 302,
    chemical_edges: 3709,
    gap_junction_pairs: 1100,
  },
  controller: {
    state: 'prototype',
    public_stream: false,
    live_broadcast_default: false,
  },
  token: {
    name: 'The Worm',
    ticker: 'TheWorm',
    paired_asset: 'PFE',
    launched: false,
  },
  worm_language_model: {
    phase: 1,
    reservoir_verified: true,
    chat_deployed: false,
  },
};

export default function handler(req, res) {
  res.setHeader('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=300');
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ ok: false, error: 'method not allowed' });
  }
  return res.status(200).json(state);
}
