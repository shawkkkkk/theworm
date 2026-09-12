import numpy as np
from worm_sim import WormBrain


class WormChemotaxis:
    def __init__(self, fov=140):
        self.fov = fov
        self.prev_lum = None

    def look(self, img, cx, cy, max_drive=6.0):
        H, W = img.shape
        half = self.fov // 2
        x0, x1 = max(0, int(cx - half)), min(W, int(cx + half))
        y0, y1 = max(0, int(cy - half)), min(H, int(cy + half))
        patch = img[y0:y1, x0:x1]
        lum = float(patch.mean()) if patch.size else 0.5

        delta = 0.0 if self.prev_lum is None else lum - self.prev_lum
        self.prev_lum = lum

        up = max(0.0, delta) * max_drive * 20
        down = max(0.0, -delta) * max_drive * 20
        return {"signal_up": min(up, max_drive), "signal_down": min(down, max_drive),
                "lum": lum, "delta": delta}


class WormPilot:
    def __init__(self, brain=None, eye=None, settle_steps=10):
        self.brain = brain or WormBrain()
        self.eye = eye or WormChemotaxis()
        self.settle_steps = settle_steps

        b = self.brain
        self.sensory = {"signal_up": b.idx("ASEL"), "signal_down": b.idx("ASER")}
        self.motor = {
            "AVAL": b.idx("AVAL"), "AVAR": b.idx("AVAR"),
            "AVBL": b.idx("AVBL"), "AVBR": b.idx("AVBR"),
            "PVCL": b.idx("PVCL"), "PVCR": b.idx("PVCR"),
        }
        self._ava_history = []

    def step(self, img, cx, cy, stim_strength=6.0, click_threshold=1.4, detail=False):
        sample = self.eye.look(img, cx, cy, max_drive=stim_strength)

        external = np.zeros(self.brain.n)
        external[self.sensory["signal_up"]] = sample["signal_up"]
        external[self.sensory["signal_down"]] = sample["signal_down"]

        for _ in range(self.settle_steps):
            self.brain.step(external)
            external = None

        ava = (self.brain.read("AVAL") + self.brain.read("AVAR")) / 2.0
        avb = (self.brain.read("AVBL") + self.brain.read("AVBR")) / 2.0
        pvc = (self.brain.read("PVCL") + self.brain.read("PVCR")) / 2.0

        forward = (avb + pvc) / 2.0
        backward = ava
        steer = (self.brain.read("AVBR") - self.brain.read("AVBL"))

        speed = np.clip(forward - backward, -1, 1)
        dx = np.clip(steer, -1, 1) * 60.0
        dy = -speed * 60.0

        self._ava_history.append(ava)
        if len(self._ava_history) > 5:
            self._ava_history.pop(0)
        click = bool(len(self._ava_history) >= 2 and
                     ava - self._ava_history[0] > click_threshold)

        hz = {"AVA": ava, "AVB": avb, "PVC": pvc, "forward": forward,
              "backward": backward, "steer": steer}

        if not detail:
            return dx, dy, click, hz
        info = {"lum": sample["lum"], "delta": sample["delta"],
                "forward": float(max(0.0, speed)), "reverse": float(max(0.0, -speed)),
                "click": float(ava)}
        return dx, dy, click, hz, info