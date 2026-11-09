"""Branching histories: create branches from experiments, track heads."""
import time
import uuid
from typing import List, Optional

from .storage import Storage
from .experiment import Experiment
from .snapshot import SnapshotManager


class BranchManager:
    def __init__(self, storage: Storage, snapshots: SnapshotManager):
        self.storage = storage
        self.snapshots = snapshots

    def create_branch(self, name: str, from_exp: Experiment, description: str = "") -> str:
        cur = self.storage.conn.execute("SELECT name FROM branches WHERE name=?", (name,))
        if cur.fetchone():
            raise ValueError(f"branch exists: {name}")
        branch_exp = Experiment.new(
            name=f"{from_exp.name} [{name}]",
            seed=from_exp.seed,
            params=dict(from_exp.params),
            parent_id=from_exp.id,
            branch_name=name,
            description=description or f"branched from {from_exp.id}",
        )
        branch_exp.state = dict(from_exp.state)
        branch_exp.metadata = dict(from_exp.metadata)
        self.snapshots.create(branch_exp)
        self.storage.conn.execute(
            "INSERT INTO branches (name, head_experiment_id, created_at, description) VALUES (?,?,?,?)",
            (name, branch_exp.id, time.time(), description),
        )
        self.storage.conn.commit()
        return branch_exp.id

    def list_branches(self) -> List[dict]:
        cur = self.storage.conn.execute("SELECT * FROM branches ORDER BY created_at")
        return [dict(r) for r in cur.fetchall()]

    def head(self, name: str) -> Optional[str]:
        cur = self.storage.conn.execute(
            "SELECT head_experiment_id FROM branches WHERE name=?", (name,))
        row = cur.fetchone()
        return row["head_experiment_id"] if row else None

    def advance_head(self, name: str, exp_id: str):
        self.storage.conn.execute(
            "UPDATE branches SET head_experiment_id=? WHERE name=?", (exp_id, name))
        self.storage.conn.commit()

    def experiments_on_branch(self, name: str) -> List[Experiment]:
        cur = self.storage.conn.execute(
            "SELECT state_blob FROM experiments WHERE branch_name=? ORDER BY created_at", (name,))
        out = []
        for r in cur.fetchall():
            try:
                out.append(self.snapshots.restore(r["state_blob"]))
            except Exception:
                pass
        return out

    def all_experiments(self) -> List[Experiment]:
        cur = self.storage.conn.execute("SELECT state_blob FROM experiments ORDER BY created_at")
        out = []
        for r in cur.fetchall():
            try:
                out.append(self.snapshots.restore(r["state_blob"]))
            except Exception:
                pass
        return out
