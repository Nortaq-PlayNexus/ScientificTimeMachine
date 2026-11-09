"""Application controller tying storage, snapshots, branches, replay, compare."""
from pathlib import Path
from typing import List, Optional

from .core.storage import Storage
from .core.experiment import Experiment
from .core.snapshot import SnapshotManager
from .core.branch import BranchManager
from .core.replay import ReplayEngine, run_simulation
from .core.compare import compare_experiments
from .core.package import export_package, import_package
from .core.recovery import rebuild_index, check_integrity


class AppController:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.storage = Storage(self.data_dir)
        self.snapshots = SnapshotManager(self.storage)
        self.branches = BranchManager(self.storage, self.snapshots)
        self.replay = ReplayEngine(self.storage)
        self._ensure_main()

    def _ensure_main(self):
        cur = self.storage.conn.execute("SELECT name FROM branches WHERE name='main'")
        if not cur.fetchone():
            e = Experiment.new("Initial Experiment", seed=42, params={"steps": 50, "noise": 0.1, "base": 1.0}, branch_name="main")
            self.snapshots.create(e)
            self.storage.conn.execute(
                "INSERT INTO branches (name, head_experiment_id, created_at, description) VALUES (?,?,?,?)",
                ("main", e.id, e.created_at, "default branch"),
            )
            self.storage.conn.commit()

    def new_experiment(self, name, seed=None, params=None, parent_id=None, branch_name="main") -> Experiment:
        e = Experiment.new(name, seed=seed, params=params, parent_id=parent_id, branch_name=branch_name)
        self.snapshots.create(e)
        try:
            self.branches.advance_head(branch_name, e.id)
        except Exception:
            pass
        return e

    def branch_from(self, exp: Experiment, name: str) -> Experiment:
        eid = self.branches.create_branch(name, exp)
        cur = self.storage.conn.execute("SELECT state_blob FROM experiments WHERE id=?", (eid,))
        row = cur.fetchone()
        return self.snapshots.restore(row["state_blob"])

    def list_experiments(self) -> List[Experiment]:
        return self.branches.all_experiments()

    def restore(self, snap_hash: str) -> Experiment:
        return self.snapshots.restore(snap_hash)

    def run(self, exp: Experiment):
        return self.replay.replay(exp)

    def compare(self, a, b):
        return compare_experiments(a, b)

    def export(self, exp, path):
        return export_package(exp, path)

    def import_package(self, path):
        e = import_package(path)
        self.snapshots.create(e)
        return e

    def integrity(self):
        return check_integrity(self.storage)

    def rebuild(self):
        return rebuild_index(self.storage)

    def close(self):
        self.storage.close()
