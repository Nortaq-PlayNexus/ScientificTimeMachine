"""Snapshot management: create, restore, verify, recover."""
import json
import time
import uuid
import hashlib
from typing import Any, Dict, Optional

from .storage import Storage
from .experiment import Experiment


class SnapshotManager:
    def __init__(self, storage: Storage):
        self.storage = storage

    def create(self, exp: Experiment) -> str:
        exp.snapshot_hash = exp.compute_hash()
        data = json.dumps(exp.to_dict(), sort_keys=True, default=str).encode()
        h = self.storage.put_blob(data)
        snap_id = str(uuid.uuid4())
        self.storage.conn.execute(
            "INSERT INTO snapshots (id, experiment_id, hash, blob_path, created_at, size) VALUES (?,?,?,?,?,?)",
            (snap_id, exp.id, h, str(self.storage.blob_path(h)), time.time(), len(data)),
        )
        self.storage.conn.execute(
            """INSERT OR REPLACE INTO experiments
            (id,name,description,created_at,parent_id,branch_name,seed,params,state_blob,snapshot_hash,metadata)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (exp.id, exp.name, exp.description, exp.created_at, exp.parent_id,
             exp.branch_name, exp.seed, json.dumps(exp.params), h, exp.snapshot_hash,
             json.dumps(exp.metadata)),
        )
        self.storage.conn.commit()
        return h

    def restore(self, snap_hash: str) -> Experiment:
        data = self.storage.get_blob(snap_hash)
        d = json.loads(data)
        if hashlib.sha256(data).hexdigest() != snap_hash:
            raise ValueError("snapshot hash mismatch")
        exp = Experiment.from_dict(d)
        if exp.compute_hash() != exp.snapshot_hash:
            raise ValueError("experiment integrity failure")
        return exp

    def verify(self, snap_hash: str) -> bool:
        try:
            data = self.storage.get_blob(snap_hash)
        except FileNotFoundError:
            return False
        if hashlib.sha256(data).hexdigest() != snap_hash:
            return False
        try:
            d = json.loads(data)
            exp = Experiment.from_dict(d)
        except Exception:
            return False
        return exp.compute_hash() == exp.snapshot_hash

    def list_for_experiment(self, exp_id: str) -> list:
        cur = self.storage.conn.execute(
            "SELECT hash, created_at, size FROM snapshots WHERE experiment_id=? ORDER BY created_at DESC",
            (exp_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    def recover_corrupt(self, snap_hash: str) -> Optional[Experiment]:
        cur = self.storage.conn.execute(
            "SELECT experiment_id FROM snapshots WHERE hash=?", (snap_hash,))
        row = cur.fetchone()
        if not row:
            return None
        exp_id = row["experiment_id"]
        cur = self.storage.conn.execute(
            "SELECT hash FROM snapshots WHERE experiment_id=? ORDER BY created_at DESC", (exp_id,))
        for r in cur.fetchall():
            h = r["hash"]
            if self.verify(h):
                return self.restore(h)
        cur = self.storage.conn.execute(
            "SELECT state_blob FROM experiments WHERE id=?", (exp_id,))
        row = cur.fetchone()
        if row:
            h = row["state_blob"]
            if self.verify(h):
                return self.restore(h)
        return None
