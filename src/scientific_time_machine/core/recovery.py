"""Corruption recovery utilities."""
import json
from pathlib import Path
from typing import Optional

from .storage import Storage
from .snapshot import SnapshotManager
from .experiment import Experiment


def rebuild_index(storage: Storage) -> int:
    count = 0
    for p in storage.blobs.rglob("*"):
        if not p.is_file():
            continue
        try:
            data = p.read_bytes()
            d = json.loads(data)
            exp = Experiment.from_dict(d)
            if exp.compute_hash() != exp.snapshot_hash:
                continue
            storage.conn.execute(
                """INSERT OR REPLACE INTO experiments
                (id,name,description,created_at,parent_id,branch_name,seed,params,state_blob,snapshot_hash,metadata)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (exp.id, exp.name, exp.description, exp.created_at, exp.parent_id,
                 exp.branch_name, exp.seed, json.dumps(exp.params), storage.put_blob(data),
                 exp.snapshot_hash, json.dumps(exp.metadata)),
            )
            count += 1
        except Exception:
            continue
    storage.conn.commit()
    return count


def check_integrity(storage: Storage) -> dict:
    issues = []
    cur = storage.conn.execute("SELECT id, state_blob, snapshot_hash FROM experiments")
    for r in cur.fetchall():
        if not storage.verify_blob(r["state_blob"]):
            issues.append({"experiment": r["id"], "issue": "missing/corrupt blob"})
    cur = storage.conn.execute("SELECT hash FROM snapshots")
    for r in cur.fetchall():
        if not storage.verify_blob(r["hash"]):
            issues.append({"snapshot": r["hash"], "issue": "corrupt snapshot blob"})
    return {"ok": len(issues) == 0, "issues": issues}
