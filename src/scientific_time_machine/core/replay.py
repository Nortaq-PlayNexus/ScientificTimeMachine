"""Deterministic simulation replay."""
import random
import json
import time
import uuid
import hashlib
from typing import Any, Dict

from .storage import Storage
from .experiment import Experiment


def run_simulation(exp: Experiment) -> Dict[str, Any]:
    rng = exp.rng()
    steps = int(exp.params.get("steps", 100))
    noise = float(exp.params.get("noise", 0.1))
    base = float(exp.params.get("base", 1.0))
    values = []
    cur = base
    for i in range(steps):
        cur = cur + (rng.random() - 0.5) * noise
        values.append(cur)
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    result = {
        "values": values,
        "mean": mean,
        "variance": variance,
        "min": min(values),
        "max": max(values),
        "steps": steps,
        "seed": exp.seed,
    }
    return result


class ReplayEngine:
    def __init__(self, storage: Storage):
        self.storage = storage

    def replay(self, exp: Experiment) -> Dict[str, Any]:
        result = run_simulation(exp)
        h = hashlib.sha256(json.dumps(result, sort_keys=True, default=str).encode()).hexdigest()
        rid = str(uuid.uuid4())
        self.storage.conn.execute(
            "INSERT INTO runs (id, experiment_id, result_blob, result_hash, created_at, status) VALUES (?,?,?,?,?,?)",
            (rid, exp.id, h, h, time.time(), "completed"),
        )
        self.storage.conn.commit()
        self.storage.put_blob(json.dumps(result, default=str).encode())
        return result

    def verify_reproducibility(self, exp: Experiment, n: int = 3) -> bool:
        results = []
        for _ in range(n):
            results.append(run_simulation(exp))
        first = json.dumps(results[0], sort_keys=True, default=str)
        return all(json.dumps(r, sort_keys=True, default=str) == first for r in results)
