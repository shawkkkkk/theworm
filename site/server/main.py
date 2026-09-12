"""Read-only public status service for TheWorm.

This service exposes project milestones only. It has no wallet, private key,
chain RPC, transaction, browser-control, or simulation-control capability.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="TheWorm public status")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


PROJECT_STATE = {
    "ok": True,
    "project": "TheWorm",
    "phase": "development",
    "connectome": {
        "source": "Cook et al. 2019 hermaphrodite",
        "neurons": 302,
        "chemical_edges": 3709,
        "gap_junction_pairs": 1100,
    },
    "controller": {
        "state": "prototype",
        "public_stream": False,
        "live_broadcast_default": False,
    },
    "token": {
        "name": "The Worm",
        "ticker": "TheWorm",
        "paired_asset": "PFE",
        "launched": False,
    },
    "worm_language_model": {
        "phase": 1,
        "reservoir_verified": True,
        "chat_deployed": False,
    },
}


@app.get("/api/state")
def api_state():
    return PROJECT_STATE


@app.get("/api/health")
def health():
    return {"ok": True, "service": "theworm-public-status"}


@app.get("/")
def root():
    return {"service": "TheWorm public status", "see": "/api/state"}
