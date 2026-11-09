"""Experiment data model with deterministic seeds and parameter versioning."""
import json
import os
import time
import uuid
import hashlib
import random
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class Experiment:
    id: str
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    parent_id: Optional[str] = None
    branch_name: str = "main"
    seed: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    snapshot_hash: str = ""

    def compute_hash(self) -> str:
        payload = {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "branch_name": self.branch_name,
            "seed": self.seed,
            "params": self.params,
            "state": self.state,
            "metadata": self.metadata,
        }
        raw = json.dumps(payload, sort_keys=True, default=str).encode()
        return hashlib.sha256(raw).hexdigest()

    def rng(self) -> random.Random:
        return random.Random(self.seed)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Experiment":
        return cls(**d)

    @staticmethod
    def new(name: str, seed: Optional[int] = None, params: Optional[Dict] = None,
            parent_id: Optional[str] = None, branch_name: str = "main",
            description: str = "") -> "Experiment":
        if seed is None:
            seed = int.from_bytes(os.urandom(8), "big")
        e = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            parent_id=parent_id,
            branch_name=branch_name,
            seed=seed,
            params=dict(params or {}),
        )
        e.snapshot_hash = e.compute_hash()
        return e
